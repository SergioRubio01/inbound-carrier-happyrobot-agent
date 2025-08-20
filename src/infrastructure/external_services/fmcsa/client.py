"""
File: client.py
Description: FMCSA API client implementation
Author: HappyRobot Team
Created: 2024-11-15
"""

import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from src.core.ports.services.fmcsa_service import FMCSAServicePort
from src.infrastructure.external_services.fmcsa.exceptions import (
    FMCSAAPIError,
    FMCSATimeoutError,
    FMCSAAuthenticationError,
    FMCSARateLimitError,
    FMCSAValidationError,
    FMCSACarrierNotFoundError,
    FMCSAServiceUnavailableError,
)
from src.infrastructure.external_services.fmcsa.models import (
    FMCSAAPIResponse,
)

logger = logging.getLogger(__name__)


class FMCSAAPIClient(FMCSAServicePort):
    """FMCSA API client implementation with retry logic and error handling."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
    ):
        """
        Initialize FMCSA API client.

        Args:
            api_key: FMCSA API key
            base_url: Base URL for FMCSA API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            backoff_factor: Exponential backoff factor
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

        # Initialize HTTP client
        self._client = None
        self._headers = {
            "Content-Type": "application/json",
            "User-Agent": "HappyRobot-FDE/1.0",
        }

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._close_client()

    async def _ensure_client(self):
        """Ensure HTTP client is initialized."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers=self._headers,
            )

    async def _close_client(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((FMCSATimeoutError, FMCSAServiceUnavailableError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> FMCSAAPIResponse:
        """
        Make HTTP request to FMCSA API with retry logic.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            FMCSAAPIResponse object

        Raises:
            Various FMCSA exceptions based on error type
        """
        await self._ensure_client()

        # Add API key to parameters
        if params is None:
            params = {}
        params["webKey"] = self.api_key

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        start_time = datetime.now()

        try:
            logger.info(f"Making FMCSA API request to {endpoint}")
            response = await self._client.get(url, params=params)
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)

            # Handle different HTTP status codes
            if response.status_code == 200:
                try:
                    data = response.json()
                    return FMCSAAPIResponse(
                        success=True,
                        data=data,
                        response_time_ms=response_time,
                    )
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON response from FMCSA API: {e}")
                    raise FMCSAValidationError(f"Invalid JSON response: {e}")

            elif response.status_code == 401:
                logger.error("FMCSA API authentication failed")
                raise FMCSAAuthenticationError("Invalid API key or authentication failed")

            elif response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "60")
                logger.warning(f"FMCSA API rate limit exceeded, retry after {retry_after}s")
                raise FMCSARateLimitError(
                    f"Rate limit exceeded, retry after {retry_after} seconds",
                    retry_after=int(retry_after)
                )

            elif response.status_code in [502, 503, 504]:
                logger.warning(f"FMCSA API service unavailable: {response.status_code}")
                raise FMCSAServiceUnavailableError(
                    f"FMCSA service unavailable: HTTP {response.status_code}"
                )

            elif response.status_code == 404:
                logger.info("Carrier not found in FMCSA system")
                raise FMCSACarrierNotFoundError("Carrier not found in FMCSA system")

            else:
                logger.error(f"FMCSA API error: HTTP {response.status_code} - {response.text}")
                raise FMCSAAPIError(
                    f"API request failed with status {response.status_code}",
                    status_code=response.status_code
                )

        except httpx.TimeoutException as e:
            logger.error(f"FMCSA API request timeout: {e}")
            raise FMCSATimeoutError(f"Request timeout after {self.timeout} seconds")

        except httpx.RequestError as e:
            logger.error(f"FMCSA API request error: {e}")
            raise FMCSAServiceUnavailableError(f"Network error: {e}")

    async def verify_carrier(
        self,
        mc_number: str
    ) -> Optional[Dict[str, Any]]:
        """
        Verify carrier eligibility and retrieve basic information.

        Args:
            mc_number: Motor Carrier number (cleaned, digits only)

        Returns:
            Dict containing carrier verification data or None if not found
        """
        try:
            # First get basic carrier information
            response = await self._make_request(
                f"carriers/docket-number/{mc_number}",
                params={}
            )

            if not response.success or not response.data:
                return None

            carrier_data = response.data

            # Parse basic carrier information
            result = {
                "mc_number": mc_number,
                "carrier_info": self._parse_carrier_info(carrier_data),
                "insurance_info": self._parse_insurance_info(carrier_data),
                "verification_timestamp": datetime.utcnow().isoformat(),
                "data_source": "FMCSA_API",
            }

            return result

        except FMCSACarrierNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error verifying carrier {mc_number}: {e}")
            raise

    async def get_safety_scores(self, mc_number: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve carrier safety scores and ratings.
        Since the main carrier endpoint includes safety data, we'll use that.

        Args:
            mc_number: Motor Carrier number (cleaned, digits only)

        Returns:
            Dict containing safety scores and ratings or None if not found
        """
        try:
            # The main carrier endpoint includes safety data
            response = await self._make_request(
                f"carriers/docket-number/{mc_number}",
                params={}
            )

            if not response.success or not response.data:
                return None

            return self._parse_safety_scores(response.data)

        except FMCSACarrierNotFoundError:
            return None

    async def get_carrier_snapshot(self, mc_number: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve comprehensive carrier information snapshot.

        Args:
            mc_number: Motor Carrier number (cleaned, digits only)

        Returns:
            Dict containing complete carrier snapshot or None if not found
        """
        try:
            # Get all available data
            basic_info = await self.verify_carrier(mc_number)
            if not basic_info:
                return None

            return {
                "mc_number": mc_number,
                "snapshot": basic_info,
                "verification_timestamp": datetime.utcnow().isoformat(),
                "data_source": "FMCSA_API",
            }

        except FMCSACarrierNotFoundError:
            return None

    async def check_insurance_status(self, mc_number: str) -> Optional[Dict[str, Any]]:
        """
        Check carrier insurance status and coverage amounts.
        Since the main carrier endpoint includes insurance data, we'll use that.

        Args:
            mc_number: Motor Carrier number (cleaned, digits only)

        Returns:
            Dict containing insurance information or None if not found
        """
        try:
            # The main carrier endpoint includes insurance data
            response = await self._make_request(
                f"carriers/docket-number/{mc_number}",
                params={}
            )

            if not response.success or not response.data:
                return None

            return self._parse_insurance_info(response.data)

        except FMCSACarrierNotFoundError:
            return None

    async def health_check(self) -> bool:
        """
        Check if the FMCSA service is available and responding.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            # Try a simple API call with a known MC number for health check (UPS)
            await self._make_request("carriers/docket-number/91029", params={})
            return True
        except Exception as e:
            logger.warning(f"FMCSA health check failed: {e}")
            return False

    def _parse_carrier_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse carrier information from FMCSA API response."""
        content = data.get("content", [])
        if not content:
            return {}

        # Extract the first content item if it's a list
        content_item = content[0] if isinstance(content, list) else content

        # The actual carrier data is nested under 'carrier' key
        carrier = content_item.get("carrier", content_item)

        # Format address from individual fields
        address_parts = []
        if carrier.get("phyStreet"):
            address_parts.append(carrier.get("phyStreet"))
        if carrier.get("phyCity"):
            address_parts.append(carrier.get("phyCity"))
        if carrier.get("phyState"):
            address_parts.append(carrier.get("phyState"))
        if carrier.get("phyZipcode"):
            address_parts.append(carrier.get("phyZipcode"))
        physical_address = ", ".join(address_parts) if address_parts else ""

        return {
            "legal_name": carrier.get("legalName", ""),
            "dba_name": carrier.get("dbaName"),
            "entity_type": carrier.get("censusTypeId", {}).get("censusTypeDesc", "CARRIER"),
            "operating_status": "ACTIVE" if carrier.get("allowedToOperate") == "Y" else "INACTIVE",
            "physical_address": physical_address,
            "phone": carrier.get("phoneNumber"),
            "out_of_service_date": carrier.get("oosDate"),
            "mcs_150_date": carrier.get("mcs150Date"),
            "mcs_150_mileage": carrier.get("mcs150Mileage"),
            "power_units": carrier.get("totalPowerUnits"),
            "drivers": carrier.get("totalDrivers"),
            "dot_number": carrier.get("dotNumber"),
            "safety_rating": carrier.get("safetyRating"),
        }

    def _parse_safety_scores(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse safety scores from FMCSA API response or extract from carrier data."""
        content = data.get("content", [])
        if not content:
            return {}

        # Extract the first content item if it's a list
        content_item = content[0] if isinstance(content, list) else content

        # The actual carrier data is nested under 'carrier' key
        carrier = content_item.get("carrier", content_item)

        # Extract safety-related metrics from carrier data
        return {
            "basic_scores": {
                "crash_total": carrier.get("crashTotal", 0),
                "fatal_crashes": carrier.get("fatalCrash", 0),
                "injury_crashes": carrier.get("injCrash", 0),
                "tow_away_crashes": carrier.get("towawayCrash", 0),
                "driver_oos_rate": carrier.get("driverOosRate", 0),
                "vehicle_oos_rate": carrier.get("vehicleOosRate", 0),
                "hazmat_oos_rate": carrier.get("hazmatOosRate", 0),
            },
            "safety_rating": carrier.get("safetyRating"),
            "rating_date": carrier.get("safetyRatingDate"),
        }

    def _parse_insurance_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse insurance information from FMCSA API response or extract from carrier data."""
        content = data.get("content", [])
        if not content:
            return {}

        # Extract the first content item if it's a list
        content_item = content[0] if isinstance(content, list) else content

        # The actual carrier data is nested under 'carrier' key
        carrier = content_item.get("carrier", content_item)

        return {
            "bipd_required": carrier.get("bipdInsuranceRequired") == "Y",
            "bipd_on_file": carrier.get("bipdInsuranceOnFile", "0"),
            "bipd_required_amount": carrier.get("bipdRequiredAmount", "0"),
            "cargo_required": carrier.get("cargoInsuranceRequired") == "Y",
            "cargo_on_file": carrier.get("cargoInsuranceOnFile", "0"),
            "bond_required": carrier.get("bondInsuranceRequired") == "Y",
            "bond_on_file": carrier.get("bondInsuranceOnFile", "0"),
        }

    def _format_address(self, address_data: Dict[str, Any]) -> str:
        """Format address from FMCSA address object."""
        if not address_data:
            return ""

        parts = []
        if address_data.get("street"):
            parts.append(address_data["street"])
        if address_data.get("city"):
            parts.append(address_data["city"])
        if address_data.get("state"):
            parts.append(address_data["state"])
        if address_data.get("zipCode"):
            parts.append(address_data["zipCode"])

        return ", ".join(parts) if parts else ""
