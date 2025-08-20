"""
Unit tests for FMCSA cache service.
"""

import pytest
from unittest.mock import AsyncMock
from datetime import timedelta

from src.infrastructure.caching.fmcsa_cache import FMCSACacheService


@pytest.fixture
def mock_cache_service():
    """Create mock cache service."""
    return AsyncMock()


@pytest.fixture
def fmcsa_cache_service(mock_cache_service):
    """Create FMCSA cache service for testing."""
    default_ttl = timedelta(hours=24)
    return FMCSACacheService(mock_cache_service, default_ttl)


class TestFMCSACacheService:
    """Test FMCSA cache service functionality."""

    def test_cache_key_generation(self, fmcsa_cache_service):
        """Test cache key generation methods."""
        mc_number = "123456"

        carrier_key = fmcsa_cache_service._get_carrier_key(mc_number)
        safety_key = fmcsa_cache_service._get_safety_key(mc_number)
        insurance_key = fmcsa_cache_service._get_insurance_key(mc_number)
        snapshot_key = fmcsa_cache_service._get_snapshot_key(mc_number)

        assert carrier_key == "fmcsa:carrier:123456"
        assert safety_key == "fmcsa:safety:123456"
        assert insurance_key == "fmcsa:insurance:123456"
        assert snapshot_key == "fmcsa:snapshot:123456"

    @pytest.mark.asyncio
    async def test_get_carrier_data_hit(self, fmcsa_cache_service, mock_cache_service):
        """Test cache hit for carrier data."""
        mc_number = "123456"
        cached_data = {
            "mc_number": mc_number,
            "carrier_info": {"legal_name": "Test Carrier"}
        }

        mock_cache_service.get.return_value = cached_data

        result = await fmcsa_cache_service.get_carrier_data(mc_number)

        assert result is not None
        assert result["cached"] is True
        assert result["cache_key"] == "fmcsa:carrier:123456"
        assert result["mc_number"] == mc_number
        mock_cache_service.get.assert_called_once_with("fmcsa:carrier:123456")

    @pytest.mark.asyncio
    async def test_get_carrier_data_miss(self, fmcsa_cache_service, mock_cache_service):
        """Test cache miss for carrier data."""
        mc_number = "123456"

        mock_cache_service.get.return_value = None

        result = await fmcsa_cache_service.get_carrier_data(mc_number)

        assert result is None
        mock_cache_service.get.assert_called_once_with("fmcsa:carrier:123456")

    @pytest.mark.asyncio
    async def test_get_carrier_data_error(self, fmcsa_cache_service, mock_cache_service):
        """Test error handling in get carrier data."""
        mc_number = "123456"

        mock_cache_service.get.side_effect = Exception("Cache error")

        result = await fmcsa_cache_service.get_carrier_data(mc_number)

        assert result is None

    @pytest.mark.asyncio
    async def test_set_carrier_data_success(self, fmcsa_cache_service, mock_cache_service):
        """Test successful carrier data caching."""
        mc_number = "123456"
        data = {
            "mc_number": mc_number,
            "carrier_info": {"legal_name": "Test Carrier"}
        }

        mock_cache_service.set.return_value = True

        result = await fmcsa_cache_service.set_carrier_data(mc_number, data)

        assert result is True
        mock_cache_service.set.assert_called_once()

        # Verify call arguments
        call_args = mock_cache_service.set.call_args
        assert call_args[0][0] == "fmcsa:carrier:123456"  # key
        cached_data = call_args[0][1]  # data
        assert cached_data["mc_number"] == mc_number
        assert "cached_at" in cached_data
        assert "cache_ttl_seconds" in cached_data
        assert "cache_source" in cached_data

    @pytest.mark.asyncio
    async def test_set_carrier_data_custom_ttl(self, fmcsa_cache_service, mock_cache_service):
        """Test carrier data caching with custom TTL."""
        mc_number = "123456"
        data = {"mc_number": mc_number}
        custom_ttl = timedelta(hours=2)

        mock_cache_service.set.return_value = True

        result = await fmcsa_cache_service.set_carrier_data(mc_number, data, custom_ttl)

        assert result is True

        # Verify TTL was passed correctly
        call_args = mock_cache_service.set.call_args
        assert call_args[0][2] == custom_ttl  # ttl parameter

    @pytest.mark.asyncio
    async def test_set_carrier_data_error(self, fmcsa_cache_service, mock_cache_service):
        """Test error handling in set carrier data."""
        mc_number = "123456"
        data = {"mc_number": mc_number}

        mock_cache_service.set.side_effect = Exception("Cache error")

        result = await fmcsa_cache_service.set_carrier_data(mc_number, data)

        assert result is False

    @pytest.mark.asyncio
    async def test_get_safety_scores_success(self, fmcsa_cache_service, mock_cache_service):
        """Test successful safety scores retrieval."""
        mc_number = "123456"
        safety_data = {"basic_scores": {"unsafe_driving": 45.2}}

        mock_cache_service.get.return_value = safety_data

        result = await fmcsa_cache_service.get_safety_scores(mc_number)

        assert result == safety_data
        mock_cache_service.get.assert_called_once_with("fmcsa:safety:123456")

    @pytest.mark.asyncio
    async def test_set_safety_scores_success(self, fmcsa_cache_service, mock_cache_service):
        """Test successful safety scores caching."""
        mc_number = "123456"
        safety_data = {"basic_scores": {"unsafe_driving": 45.2}}

        mock_cache_service.set.return_value = True

        result = await fmcsa_cache_service.set_safety_scores(mc_number, safety_data)

        assert result is True
        mock_cache_service.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_insurance_data_success(self, fmcsa_cache_service, mock_cache_service):
        """Test successful insurance data retrieval."""
        mc_number = "123456"
        insurance_data = {"bipd_required": 750000}

        mock_cache_service.get.return_value = insurance_data

        result = await fmcsa_cache_service.get_insurance_data(mc_number)

        assert result == insurance_data
        mock_cache_service.get.assert_called_once_with("fmcsa:insurance:123456")

    @pytest.mark.asyncio
    async def test_set_insurance_data_success(self, fmcsa_cache_service, mock_cache_service):
        """Test successful insurance data caching."""
        mc_number = "123456"
        insurance_data = {"bipd_required": 750000}

        mock_cache_service.set.return_value = True

        result = await fmcsa_cache_service.set_insurance_data(mc_number, insurance_data)

        assert result is True
        mock_cache_service.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_full_snapshot_success(self, fmcsa_cache_service, mock_cache_service):
        """Test successful full snapshot retrieval."""
        mc_number = "123456"
        snapshot_data = {
            "mc_number": mc_number,
            "carrier_info": {"legal_name": "Test Carrier"},
            "safety_scores": {"basic_scores": {"unsafe_driving": 45.2}},
            "insurance_info": {"bipd_required": 750000}
        }

        mock_cache_service.get.return_value = snapshot_data

        result = await fmcsa_cache_service.get_full_snapshot(mc_number)

        assert result == snapshot_data
        mock_cache_service.get.assert_called_once_with("fmcsa:snapshot:123456")

    @pytest.mark.asyncio
    async def test_set_full_snapshot_success(self, fmcsa_cache_service, mock_cache_service):
        """Test successful full snapshot caching."""
        mc_number = "123456"
        snapshot_data = {
            "mc_number": mc_number,
            "carrier_info": {"legal_name": "Test Carrier"}
        }

        mock_cache_service.set.return_value = True

        result = await fmcsa_cache_service.set_full_snapshot(mc_number, snapshot_data)

        assert result is True
        mock_cache_service.set.assert_called_once()

        # Verify cache metadata was added
        call_args = mock_cache_service.set.call_args
        cached_data = call_args[0][1]
        assert "cache_type" in cached_data
        assert cached_data["cache_type"] == "full_snapshot"

    @pytest.mark.asyncio
    async def test_invalidate_carrier_success(self, fmcsa_cache_service, mock_cache_service):
        """Test successful carrier cache invalidation."""
        mc_number = "123456"

        mock_cache_service.delete.return_value = True

        result = await fmcsa_cache_service.invalidate_carrier(mc_number)

        assert result is True
        assert mock_cache_service.delete.call_count == 4  # 4 different cache keys

        # Verify all expected keys were deleted
        expected_keys = [
            "fmcsa:carrier:123456",
            "fmcsa:safety:123456",
            "fmcsa:insurance:123456",
            "fmcsa:snapshot:123456"
        ]

        actual_keys = [call[0][0] for call in mock_cache_service.delete.call_args_list]
        assert set(actual_keys) == set(expected_keys)

    @pytest.mark.asyncio
    async def test_invalidate_carrier_partial_failure(self, fmcsa_cache_service, mock_cache_service):
        """Test carrier cache invalidation with partial failure."""
        mc_number = "123456"

        # First call succeeds, others fail
        mock_cache_service.delete.side_effect = [True, False, False, False]

        result = await fmcsa_cache_service.invalidate_carrier(mc_number)

        assert result is False
        assert mock_cache_service.delete.call_count == 4

    @pytest.mark.asyncio
    async def test_invalidate_carrier_error(self, fmcsa_cache_service, mock_cache_service):
        """Test error handling in carrier cache invalidation."""
        mc_number = "123456"

        mock_cache_service.delete.side_effect = Exception("Cache error")

        result = await fmcsa_cache_service.invalidate_carrier(mc_number)

        assert result is False

    @pytest.mark.asyncio
    async def test_check_cache_freshness_success(self, fmcsa_cache_service, mock_cache_service):
        """Test successful cache freshness check."""
        mc_number = "123456"

        # Mock exists and get_ttl responses
        mock_cache_service.exists.side_effect = [True, False, True, False]  # carrier, safety, insurance, snapshot
        mock_cache_service.get_ttl.side_effect = [3600, None, 1800, None]  # TTLs for existing entries

        result = await fmcsa_cache_service.check_cache_freshness(mc_number)

        assert result["mc_number"] == mc_number
        assert "cache_status" in result

        cache_status = result["cache_status"]

        # Carrier data cached with TTL
        assert cache_status["carrier"]["cached"] is True
        assert cache_status["carrier"]["ttl_seconds"] == 3600
        assert cache_status["carrier"]["expires_in"] == "3600s"

        # Safety data not cached
        assert cache_status["safety"]["cached"] is False
        assert cache_status["safety"]["ttl_seconds"] is None

        # Insurance data cached with TTL
        assert cache_status["insurance"]["cached"] is True
        assert cache_status["insurance"]["ttl_seconds"] == 1800

        # Snapshot data not cached
        assert cache_status["snapshot"]["cached"] is False

    @pytest.mark.asyncio
    async def test_check_cache_freshness_with_errors(self, fmcsa_cache_service, mock_cache_service):
        """Test cache freshness check with errors."""
        mc_number = "123456"

        # Mock error for one of the checks
        mock_cache_service.exists.side_effect = [True, Exception("Cache error"), True, True]
        mock_cache_service.get_ttl.side_effect = [3600, None, 1800, 7200]

        result = await fmcsa_cache_service.check_cache_freshness(mc_number)

        assert result["mc_number"] == mc_number
        cache_status = result["cache_status"]

        # First entry should be successful
        assert cache_status["carrier"]["cached"] is True

        # Second entry should have error
        assert cache_status["safety"]["cached"] is False
        assert "error" in cache_status["safety"]

        # Other entries should be successful
        assert cache_status["insurance"]["cached"] is True
        assert cache_status["snapshot"]["cached"] is True
