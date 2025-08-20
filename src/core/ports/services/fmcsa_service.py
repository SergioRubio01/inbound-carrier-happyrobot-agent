"""
File: fmcsa_service.py
Description: Port interface for FMCSA external service integration
Author: HappyRobot Team
Created: 2024-11-15
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class FMCSAServicePort(ABC):
    """Port interface for FMCSA external service integration.

    This interface defines the contract for integrating with the FMCSA WebServices API
    to fetch carrier information, safety scores, and insurance data.
    """

    @abstractmethod
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

        Raises:
            FMCSAServiceError: When API call fails or returns invalid data
        """
        pass

    @abstractmethod
    async def get_safety_scores(
        self,
        mc_number: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve carrier safety scores and ratings.

        Args:
            mc_number: Motor Carrier number (cleaned, digits only)

        Returns:
            Dict containing safety scores and ratings or None if not found

        Raises:
            FMCSAServiceError: When API call fails or returns invalid data
        """
        pass

    @abstractmethod
    async def get_carrier_snapshot(
        self,
        mc_number: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve comprehensive carrier information snapshot.

        Args:
            mc_number: Motor Carrier number (cleaned, digits only)

        Returns:
            Dict containing complete carrier snapshot or None if not found

        Raises:
            FMCSAServiceError: When API call fails or returns invalid data
        """
        pass

    @abstractmethod
    async def check_insurance_status(
        self,
        mc_number: str
    ) -> Optional[Dict[str, Any]]:
        """
        Check carrier insurance status and coverage amounts.

        Args:
            mc_number: Motor Carrier number (cleaned, digits only)

        Returns:
            Dict containing insurance information or None if not found

        Raises:
            FMCSAServiceError: When API call fails or returns invalid data
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the FMCSA service is available and responding.

        Returns:
            True if service is healthy, False otherwise
        """
        pass
