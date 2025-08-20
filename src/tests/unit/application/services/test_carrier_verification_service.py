"""
Unit tests for carrier verification service.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from src.core.application.services.carrier_verification_service import CarrierVerificationService
from src.infrastructure.external_services.fmcsa.exceptions import (
    FMCSAAuthenticationError,
    FMCSATimeoutError,
)


@pytest.fixture
def mock_fmcsa_service():
    """Create mock FMCSA service."""
    return AsyncMock()


@pytest.fixture
def mock_carrier_repository():
    """Create mock carrier repository."""
    return AsyncMock()


@pytest.fixture
def mock_cache_service():
    """Create mock cache service."""
    return AsyncMock()


@pytest.fixture
def verification_service(mock_fmcsa_service, mock_carrier_repository, mock_cache_service):
    """Create carrier verification service for testing."""
    return CarrierVerificationService(
        fmcsa_service=mock_fmcsa_service,
        carrier_repository=mock_carrier_repository,
        cache_service=mock_cache_service,
        enable_cache=True,
        database_fallback_max_age_days=7,
    )


@pytest.fixture
def verification_service_no_cache(mock_fmcsa_service, mock_carrier_repository, mock_cache_service):
    """Create carrier verification service without caching."""
    return CarrierVerificationService(
        fmcsa_service=mock_fmcsa_service,
        carrier_repository=mock_carrier_repository,
        cache_service=mock_cache_service,
        enable_cache=False,
        database_fallback_max_age_days=7,
    )


class TestCarrierVerificationService:
    """Test carrier verification service functionality."""

    @pytest.mark.asyncio
    async def test_verify_carrier_invalid_mc_number(self, verification_service):
        """Test verification with invalid MC number."""
        result = await verification_service.verify_carrier("abc")

        assert result["eligible"] is False
        assert result["reason"] == "Invalid MC number format"
        assert result["verification_source"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_verify_carrier_cache_hit(self, verification_service, mock_cache_service):
        """Test verification with cache hit."""
        mc_number = "123456"
        cached_data = {
            "mc_number": mc_number,
            "eligible": True,
            "carrier_info": {"legal_name": "Test Carrier"},
            "verification_source": "CACHE"
        }

        mock_cache_service.get_carrier_data.return_value = cached_data

        result = await verification_service.verify_carrier(mc_number)

        assert result["eligible"] is True
        assert result["verification_source"] == "CACHE"
        assert result["carrier_info"]["legal_name"] == "Test Carrier"
        mock_cache_service.get_carrier_data.assert_called_once_with(mc_number)

    @pytest.mark.asyncio
    async def test_verify_carrier_cache_hit_with_safety(self, verification_service, mock_cache_service):
        """Test verification with cache hit including safety scores."""
        mc_number = "123456"
        cached_data = {
            "mc_number": mc_number,
            "eligible": True,
            "carrier_info": {"legal_name": "Test Carrier"},
            "verification_source": "CACHE"
        }
        safety_data = {"basic_scores": {"unsafe_driving": 45.2}}

        mock_cache_service.get_carrier_data.return_value = cached_data
        mock_cache_service.get_safety_scores.return_value = safety_data

        result = await verification_service.verify_carrier(mc_number)

        assert result["eligible"] is True
        assert result["safety_score"] == safety_data
        mock_cache_service.get_safety_scores.assert_called_once_with(mc_number)

    @pytest.mark.asyncio
    async def test_verify_carrier_api_success(self, verification_service, mock_fmcsa_service, mock_cache_service):
        """Test verification with successful API call."""
        mc_number = "123456"
        api_data = {
            "mc_number": mc_number,
            "carrier_info": {"legal_name": "API Carrier"},
            "safety_scores": {"basic_scores": {"unsafe_driving": 30.5}},
            "insurance_info": {"bipd_required": 750000}
        }

        mock_cache_service.get_carrier_data.return_value = None  # Cache miss
        mock_fmcsa_service.verify_carrier.return_value = api_data
        mock_cache_service.set_carrier_data.return_value = True

        result = await verification_service.verify_carrier(mc_number)

        assert result["eligible"] is True
        assert result["verification_source"] == "FMCSA_API"
        assert result["carrier_info"]["legal_name"] == "API Carrier"
        assert result["cached"] is False

        # Verify caching was attempted
        mock_cache_service.set_carrier_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_carrier_api_failure_db_fallback(
        self, verification_service, mock_fmcsa_service, mock_carrier_repository, mock_cache_service
    ):
        """Test verification with API failure and database fallback."""
        mc_number = "123456"

        # Mock carrier entity
        mock_carrier = MagicMock()
        mock_carrier.is_eligible = True
        mock_carrier.legal_name = "DB Carrier"
        mock_carrier.dba_name = "DB Trucking"
        mock_carrier.entity_type = "CARRIER"
        mock_carrier.operating_status = "AUTHORIZED_FOR_HIRE"
        mock_carrier.address = MagicMock()
        mock_carrier.address.city = "Dallas"
        mock_carrier.address.state = "TX"
        mock_carrier.primary_contact = {"phone": "(214) 555-0100"}
        mock_carrier.safety_scores = {"basic_score": 75}
        mock_carrier.updated_at = datetime.utcnow() - timedelta(days=1)  # Recent data

        mock_cache_service.get_carrier_data.return_value = None  # Cache miss
        mock_fmcsa_service.verify_carrier.return_value = None  # API failure
        mock_carrier_repository.get_by_mc_number.return_value = mock_carrier

        result = await verification_service.verify_carrier(mc_number)

        assert result["eligible"] is True
        assert result["verification_source"] == "DATABASE_FALLBACK"
        assert result["carrier_info"]["legal_name"] == "DB Carrier"
        assert "warning" in result

    @pytest.mark.asyncio
    async def test_verify_carrier_not_found_anywhere(
        self, verification_service, mock_fmcsa_service, mock_carrier_repository, mock_cache_service
    ):
        """Test verification when carrier is not found anywhere."""
        mc_number = "999999"

        mock_cache_service.get_carrier_data.return_value = None  # Cache miss
        mock_fmcsa_service.verify_carrier.return_value = None  # API not found
        mock_carrier_repository.get_by_mc_number.return_value = None  # DB not found

        result = await verification_service.verify_carrier(mc_number)

        assert result["eligible"] is False
        assert result["verification_source"] == "NOT_FOUND"
        assert result["reason"] == "MC number not found"

    @pytest.mark.asyncio
    async def test_verify_carrier_authentication_error(
        self, verification_service, mock_fmcsa_service, mock_cache_service
    ):
        """Test verification with authentication error (should be raised)."""
        mc_number = "123456"

        mock_cache_service.get_carrier_data.return_value = None
        mock_fmcsa_service.verify_carrier.side_effect = FMCSAAuthenticationError("Invalid API key")

        with pytest.raises(FMCSAAuthenticationError):
            await verification_service.verify_carrier(mc_number)

    @pytest.mark.asyncio
    async def test_verify_carrier_timeout_with_fallback(
        self, verification_service, mock_fmcsa_service, mock_carrier_repository, mock_cache_service
    ):
        """Test verification with timeout and successful fallback."""
        mc_number = "123456"

        # Mock carrier for fallback
        mock_carrier = MagicMock()
        mock_carrier.is_eligible = True
        mock_carrier.legal_name = "Fallback Carrier"
        mock_carrier.dba_name = None
        mock_carrier.entity_type = "CARRIER"
        mock_carrier.operating_status = "AUTHORIZED_FOR_HIRE"
        mock_carrier.address = None
        mock_carrier.primary_contact = None
        mock_carrier.safety_scores = None
        mock_carrier.updated_at = datetime.utcnow() - timedelta(days=2)

        mock_cache_service.get_carrier_data.return_value = None
        mock_fmcsa_service.verify_carrier.side_effect = FMCSATimeoutError("Request timeout")
        mock_carrier_repository.get_by_mc_number.return_value = mock_carrier

        result = await verification_service.verify_carrier(mc_number)

        assert result["eligible"] is True
        assert result["verification_source"] == "DATABASE_FALLBACK"
        assert "warning" in result

    @pytest.mark.asyncio
    async def test_verify_carrier_no_cache_enabled(
        self, verification_service_no_cache, mock_fmcsa_service, mock_cache_service
    ):
        """Test verification with caching disabled."""
        mc_number = "123456"
        api_data = {
            "mc_number": mc_number,
            "carrier_info": {"legal_name": "API Carrier"}
        }

        mock_fmcsa_service.verify_carrier.return_value = api_data

        result = await verification_service_no_cache.verify_carrier(mc_number)

        assert result["eligible"] is True
        assert result["verification_source"] == "FMCSA_API"

        # Verify cache was not accessed
        mock_cache_service.get_carrier_data.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_carrier_snapshot_success(self, verification_service, mock_fmcsa_service, mock_cache_service):
        """Test successful carrier snapshot retrieval."""
        mc_number = "123456"
        snapshot_data = {
            "mc_number": mc_number,
            "snapshot": {
                "carrier_info": {"legal_name": "Snapshot Carrier"},
                "safety_scores": {"basic_scores": {"unsafe_driving": 25.0}},
                "insurance_info": {"bipd_required": 750000}
            }
        }

        mock_cache_service.get_full_snapshot.return_value = None  # Cache miss
        mock_fmcsa_service.get_carrier_snapshot.return_value = snapshot_data
        mock_cache_service.set_full_snapshot.return_value = True

        result = await verification_service.get_carrier_snapshot(mc_number)

        assert result["eligible"] is True
        assert result["carrier_info"]["legal_name"] == "Snapshot Carrier"
        assert result["safety_score"]["basic_scores"]["unsafe_driving"] == 25.0
        assert result["verification_source"] == "FMCSA_API"

        # Verify caching was attempted
        mock_cache_service.set_full_snapshot.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_carrier_snapshot_cached(self, verification_service, mock_cache_service):
        """Test carrier snapshot retrieval from cache."""
        mc_number = "123456"
        cached_snapshot = {
            "mc_number": mc_number,
            "carrier_info": {"legal_name": "Cached Carrier"}
        }

        mock_cache_service.get_full_snapshot.return_value = cached_snapshot

        result = await verification_service.get_carrier_snapshot(mc_number)

        assert result["cached"] is True
        assert result["carrier_info"]["legal_name"] == "Cached Carrier"

    @pytest.mark.asyncio
    async def test_check_service_health_all_healthy(
        self, verification_service, mock_fmcsa_service, mock_cache_service, mock_carrier_repository
    ):
        """Test service health check with all services healthy."""
        mock_fmcsa_service.health_check.return_value = True
        mock_cache_service.cache_service.set.return_value = True
        mock_cache_service.cache_service.get.return_value = "test"
        mock_cache_service.cache_service.delete.return_value = True
        mock_carrier_repository.get_by_mc_number.return_value = None  # No error

        result = await verification_service.check_service_health()

        assert result["overall_status"] == "healthy"
        assert result["services"]["fmcsa_api"]["status"] == "healthy"
        assert result["services"]["cache"]["status"] == "healthy"
        assert result["services"]["database"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_check_service_health_fmcsa_unhealthy(
        self, verification_service, mock_fmcsa_service, mock_cache_service, mock_carrier_repository
    ):
        """Test service health check with FMCSA API unhealthy."""
        mock_fmcsa_service.health_check.return_value = False
        mock_cache_service.cache_service.set.return_value = True
        mock_cache_service.cache_service.get.return_value = "test"
        mock_cache_service.cache_service.delete.return_value = True
        mock_carrier_repository.get_by_mc_number.return_value = None

        result = await verification_service.check_service_health()

        assert result["overall_status"] == "degraded"
        assert result["services"]["fmcsa_api"]["status"] == "unhealthy"
        assert result["services"]["cache"]["status"] == "healthy"
        assert result["services"]["database"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_check_service_health_database_error(
        self, verification_service, mock_fmcsa_service, mock_cache_service, mock_carrier_repository
    ):
        """Test service health check with database error."""
        mock_fmcsa_service.health_check.return_value = True
        mock_cache_service.cache_service.set.return_value = True
        mock_cache_service.cache_service.get.return_value = "test"
        mock_cache_service.cache_service.delete.return_value = True
        mock_carrier_repository.get_by_mc_number.side_effect = Exception("DB error")

        result = await verification_service.check_service_health()

        assert result["overall_status"] == "degraded"
        assert result["services"]["fmcsa_api"]["status"] == "healthy"
        assert result["services"]["cache"]["status"] == "healthy"
        assert result["services"]["database"]["status"] == "error"

    @pytest.mark.asyncio
    async def test_invalidate_carrier_cache_success(self, verification_service, mock_cache_service):
        """Test successful cache invalidation."""
        mc_number = "123456"
        mock_cache_service.invalidate_carrier.return_value = True

        result = await verification_service.invalidate_carrier_cache(mc_number)

        assert result is True
        mock_cache_service.invalidate_carrier.assert_called_once_with(mc_number)

    @pytest.mark.asyncio
    async def test_invalidate_carrier_cache_disabled(self, verification_service_no_cache, mock_cache_service):
        """Test cache invalidation when caching is disabled."""
        mc_number = "123456"

        result = await verification_service_no_cache.invalidate_carrier_cache(mc_number)

        assert result is True
        mock_cache_service.invalidate_carrier.assert_not_called()

    @pytest.mark.asyncio
    async def test_database_fallback_old_data(
        self, verification_service, mock_fmcsa_service, mock_carrier_repository, mock_cache_service
    ):
        """Test database fallback with old data (exceeds max age)."""
        mc_number = "123456"

        # Mock old carrier data
        mock_carrier = MagicMock()
        mock_carrier.is_eligible = True
        mock_carrier.legal_name = "Old Carrier"
        mock_carrier.dba_name = None
        mock_carrier.entity_type = "CARRIER"
        mock_carrier.operating_status = "AUTHORIZED_FOR_HIRE"
        mock_carrier.address = None
        mock_carrier.primary_contact = None
        mock_carrier.safety_scores = None
        mock_carrier.updated_at = datetime.utcnow() - timedelta(days=10)  # Too old

        mock_cache_service.get_carrier_data.return_value = None
        mock_fmcsa_service.verify_carrier.return_value = None
        mock_carrier_repository.get_by_mc_number.return_value = mock_carrier

        with patch('src.core.application.services.carrier_verification_service.logger') as mock_logger:
            result = await verification_service.verify_carrier(mc_number)

            # Should still return the data but with warning logged
            assert result["eligible"] is True
            assert result["verification_source"] == "DATABASE_FALLBACK"
            mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_cache_api_response_error_handling(
        self, verification_service, mock_fmcsa_service, mock_cache_service
    ):
        """Test error handling during cache write after successful API call."""
        mc_number = "123456"
        api_data = {
            "mc_number": mc_number,
            "carrier_info": {"legal_name": "API Carrier"},
            "safety_score": {"basic_scores": {"unsafe_driving": 30.5}},
            "insurance_info": {"bipd_required": 750000}
        }

        mock_cache_service.get_carrier_data.return_value = None
        mock_fmcsa_service.verify_carrier.return_value = api_data
        mock_cache_service.set_carrier_data.side_effect = Exception("Cache write error")

        # Should still return successful result even if caching fails
        result = await verification_service.verify_carrier(mc_number)

        assert result["eligible"] is True
        assert result["verification_source"] == "FMCSA_API"
