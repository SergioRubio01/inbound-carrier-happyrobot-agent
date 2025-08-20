"""
Unit tests for FMCSA API client.
"""

import pytest
from unittest.mock import patch, MagicMock
import httpx

from src.infrastructure.external_services.fmcsa.client import FMCSAAPIClient
from src.infrastructure.external_services.fmcsa.exceptions import (
    FMCSATimeoutError,
    FMCSAAuthenticationError,
    FMCSARateLimitError,
    FMCSAValidationError,
    FMCSAServiceUnavailableError,
)


@pytest.fixture
def fmcsa_client():
    """Create FMCSA client for testing."""
    return FMCSAAPIClient(
        api_key="test-api-key",
        base_url="https://test.fmcsa.api",
        timeout=30,
        max_retries=2,
        backoff_factor=1.0,
    )


@pytest.fixture
def mock_http_response():
    """Mock HTTP response."""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "content": [{
            "carrier": {
                "legalName": "Test Carrier LLC",
                "dbaName": "Test Trucking",
                "censusTypeId": {
                    "censusType": "C",
                    "censusTypeDesc": "CARRIER",
                    "censusTypeId": 1
                },
                "allowedToOperate": "Y",
                "phyStreet": "123 Main St",
                "phyCity": "Dallas",
                "phyState": "TX",
                "phyZipcode": "75201",
                "phoneNumber": "(214) 555-0100",
                "oosDate": None,
                "mcs150Date": "2024-06-15",
                "mcs150Mileage": 250000,
                "totalPowerUnits": 50,
                "totalDrivers": 25,
                "dotNumber": 2952744,
                "safetyRating": "SATISFACTORY",
                "bipdInsuranceRequired": "Y",
                "bipdInsuranceOnFile": "750",
                "bipdRequiredAmount": "750",
                "cargoInsuranceRequired": "u",
                "cargoInsuranceOnFile": "0",
                "bondInsuranceRequired": "u",
                "bondInsuranceOnFile": "0"
            }
        }],
        "retrievalDate": "2025-08-20T00:33:14.939+0000"
    }
    return response


class TestFMCSAAPIClient:
    """Test FMCSA API client functionality."""

    @pytest.mark.asyncio
    async def test_verify_carrier_success(self, fmcsa_client, mock_http_response):
        """Test successful carrier verification."""
        with patch.object(fmcsa_client, '_ensure_client'):
            with patch.object(fmcsa_client, '_client') as mock_client:
                mock_client.get.return_value = mock_http_response

                result = await fmcsa_client.verify_carrier("123456")

                assert result is not None
                assert result["mc_number"] == "123456"
                assert result["carrier_info"]["legal_name"] == "Test Carrier LLC"
                assert result["carrier_info"]["dba_name"] == "Test Trucking"
                assert result["verification_timestamp"] is not None
                assert result["data_source"] == "FMCSA_API"
                assert result["insurance_info"] is not None
                assert result["insurance_info"]["bipd_required"] is True
                assert result["insurance_info"]["bipd_on_file"] == "750"

    @pytest.mark.asyncio
    async def test_verify_carrier_with_insurance_info(self, fmcsa_client, mock_http_response):
        """Test carrier verification includes insurance information."""
        with patch.object(fmcsa_client, '_ensure_client'):
            with patch.object(fmcsa_client, '_client') as mock_client:
                mock_client.get.return_value = mock_http_response

                result = await fmcsa_client.verify_carrier("123456")

                assert result is not None
                assert result["insurance_info"] is not None
                assert result["insurance_info"]["bipd_required"] is True
                assert result["insurance_info"]["bipd_on_file"] == "750"
                assert result["insurance_info"]["bipd_required_amount"] == "750"

    @pytest.mark.asyncio
    async def test_verify_carrier_not_found(self, fmcsa_client):
        """Test carrier not found scenario."""
        with patch.object(fmcsa_client, '_ensure_client'):
            with patch.object(fmcsa_client, '_client') as mock_client:
                response = MagicMock()
                response.status_code = 404
                mock_client.get.return_value = response

                result = await fmcsa_client.verify_carrier("999999")

                assert result is None

    @pytest.mark.asyncio
    async def test_authentication_error(self, fmcsa_client):
        """Test authentication error handling."""
        with patch.object(fmcsa_client, '_ensure_client'):
            with patch.object(fmcsa_client, '_client') as mock_client:
                response = MagicMock()
                response.status_code = 401
                mock_client.get.return_value = response

                with pytest.raises(FMCSAAuthenticationError):
                    await fmcsa_client.verify_carrier("123456")

    @pytest.mark.asyncio
    async def test_rate_limit_error(self, fmcsa_client):
        """Test rate limit error handling."""
        with patch.object(fmcsa_client, '_ensure_client'):
            with patch.object(fmcsa_client, '_client') as mock_client:
                response = MagicMock()
                response.status_code = 429
                response.headers = {"Retry-After": "60"}
                mock_client.get.return_value = response

                with pytest.raises(FMCSARateLimitError) as exc_info:
                    await fmcsa_client.verify_carrier("123456")

                assert exc_info.value.retry_after == 60

    @pytest.mark.asyncio
    async def test_service_unavailable_error(self, fmcsa_client):
        """Test service unavailable error handling."""
        with patch.object(fmcsa_client, '_ensure_client'):
            with patch.object(fmcsa_client, '_client') as mock_client:
                response = MagicMock()
                response.status_code = 503
                mock_client.get.return_value = response

                with pytest.raises(FMCSAServiceUnavailableError):
                    await fmcsa_client.verify_carrier("123456")

    @pytest.mark.asyncio
    async def test_timeout_error(self, fmcsa_client):
        """Test timeout error handling."""
        with patch.object(fmcsa_client, '_ensure_client'):
            with patch.object(fmcsa_client, '_client') as mock_client:
                mock_client.get.side_effect = httpx.TimeoutException("Request timeout")

                with pytest.raises(FMCSATimeoutError):
                    await fmcsa_client.verify_carrier("123456")

    @pytest.mark.asyncio
    async def test_invalid_json_response(self, fmcsa_client):
        """Test invalid JSON response handling."""
        with patch.object(fmcsa_client, '_ensure_client'):
            with patch.object(fmcsa_client, '_client') as mock_client:
                response = MagicMock()
                response.status_code = 200
                response.json.side_effect = ValueError("Invalid JSON")
                mock_client.get.return_value = response

                with pytest.raises(FMCSAValidationError):
                    await fmcsa_client.verify_carrier("123456")

    @pytest.mark.asyncio
    async def test_get_safety_scores_success(self, fmcsa_client):
        """Test successful safety scores retrieval."""
        safety_response = MagicMock()
        safety_response.status_code = 200
        safety_response.json.return_value = {
            "content": [{
                "unsafeDriving": 45.2,
                "hoursOfService": 38.1,
                "vehicleMaintenance": 52.3,
                "controlledSubstances": 0,
                "hazmat": None,
                "driverFitness": 41.7,
                "crashIndicator": 28.9,
                "safetyRating": "SATISFACTORY",
                "ratingDate": "2024-03-20"
            }]
        }

        with patch.object(fmcsa_client, '_ensure_client'):
            with patch.object(fmcsa_client, '_client') as mock_client:
                mock_client.get.return_value = safety_response

                result = await fmcsa_client.get_safety_scores("123456")

                assert result is not None
                assert result["basic_scores"]["unsafe_driving"] == 45.2
                assert result["safety_rating"] == "SATISFACTORY"

    @pytest.mark.asyncio
    async def test_check_insurance_status_success(self, fmcsa_client):
        """Test successful insurance status check."""
        insurance_response = MagicMock()
        insurance_response.status_code = 200
        insurance_response.json.return_value = {
            "content": [{
                "bipdRequired": 750000,
                "bipdOnFile": 1000000,
                "cargoRequired": 100000,
                "cargoOnFile": 150000,
                "bondRequired": 0,
                "bondOnFile": 0
            }]
        }

        with patch.object(fmcsa_client, '_ensure_client'):
            with patch.object(fmcsa_client, '_client') as mock_client:
                mock_client.get.return_value = insurance_response

                result = await fmcsa_client.check_insurance_status("123456")

                assert result is not None
                assert result["bipd_required"] == 750000
                assert result["bipd_on_file"] == 1000000
                assert result["cargo_required"] == 100000
                assert result["cargo_on_file"] == 150000

    @pytest.mark.asyncio
    async def test_health_check_success(self, fmcsa_client):
        """Test successful health check."""
        with patch.object(fmcsa_client, '_ensure_client'):
            with patch.object(fmcsa_client, '_client') as mock_client:
                response = MagicMock()
                response.status_code = 200
                mock_client.get.return_value = response

                result = await fmcsa_client.health_check()

                assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, fmcsa_client):
        """Test health check failure."""
        with patch.object(fmcsa_client, '_ensure_client'):
            with patch.object(fmcsa_client, '_client') as mock_client:
                mock_client.get.side_effect = Exception("Connection failed")

                result = await fmcsa_client.health_check()

                assert result is False

    def test_format_address(self, fmcsa_client):
        """Test address formatting."""
        address_data = {
            "street": "123 Main St",
            "city": "Dallas",
            "state": "TX",
            "zipCode": "75201"
        }

        result = fmcsa_client._format_address(address_data)

        assert result == "123 Main St, Dallas, TX, 75201"

    def test_format_address_empty(self, fmcsa_client):
        """Test empty address formatting."""
        result = fmcsa_client._format_address({})
        assert result == ""

    def test_parse_carrier_info(self, fmcsa_client):
        """Test carrier info parsing."""
        data = {
            "content": [{
                "legalName": "Test Carrier LLC",
                "dbaName": "Test Trucking",
                "entityType": "CARRIER",
                "operatingStatus": "AUTHORIZED_FOR_HIRE",
                "phyAddress": {
                    "street": "123 Main St",
                    "city": "Dallas",
                    "state": "TX",
                    "zipCode": "75201"
                },
                "phoneNumber": "(214) 555-0100",
                "outOfServiceDate": None,
                "mcs150Date": "2024-06-15",
                "mcs150Mileage": 250000,
                "totalPowerUnits": 50,
                "totalDrivers": 25
            }]
        }

        result = fmcsa_client._parse_carrier_info(data)

        assert result["legal_name"] == "Test Carrier LLC"
        assert result["dba_name"] == "Test Trucking"
        assert result["entity_type"] == "CARRIER"
        assert result["operating_status"] == "AUTHORIZED_FOR_HIRE"
        assert result["physical_address"] == "123 Main St, Dallas, TX, 75201"
        assert result["phone"] == "(214) 555-0100"
        assert result["mcs_150_date"] == "2024-06-15"
        assert result["mcs_150_mileage"] == 250000
        assert result["power_units"] == 50
        assert result["drivers"] == 25
