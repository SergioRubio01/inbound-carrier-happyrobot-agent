"""
File: carrier_repository.py
Description: Carrier repository port interface
Author: HappyRobot Team
Created: 2024-08-14
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import date

from src.core.domain.entities import Carrier
from src.core.domain.value_objects import MCNumber


class ICarrierRepository(ABC):
    """Port interface for carrier repository."""

    @abstractmethod
    async def create(self, carrier: Carrier) -> Carrier:
        """Create a new carrier."""
        pass

    @abstractmethod
    async def get_by_id(self, carrier_id: UUID) -> Optional[Carrier]:
        """Get carrier by ID."""
        pass

    @abstractmethod
    async def get_by_mc_number(self, mc_number: MCNumber) -> Optional[Carrier]:
        """Get carrier by MC number."""
        pass

    @abstractmethod
    async def update(self, carrier: Carrier) -> Carrier:
        """Update existing carrier."""
        pass

    @abstractmethod
    async def delete(self, carrier_id: UUID) -> bool:
        """Delete carrier (soft delete)."""
        pass

    @abstractmethod
    async def get_eligible_carriers(self, limit: int = 100, offset: int = 0) -> List[Carrier]:
        """Get list of eligible carriers."""
        pass

    @abstractmethod
    async def search_carriers(self,
                            legal_name: Optional[str] = None,
                            operating_status: Optional[str] = None,
                            limit: int = 100,
                            offset: int = 0) -> List[Carrier]:
        """Search carriers by criteria."""
        pass

    @abstractmethod
    async def exists_by_mc_number(self, mc_number: MCNumber) -> bool:
        """Check if carrier exists by MC number."""
        pass

    @abstractmethod
    async def get_carrier_metrics(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get aggregated carrier metrics for date range."""
        pass
