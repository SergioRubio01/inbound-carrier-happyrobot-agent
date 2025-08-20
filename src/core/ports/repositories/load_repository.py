"""
File: load_repository.py
Description: Load repository port interface
Author: HappyRobot Team
Created: 2024-08-14
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import date

from src.core.domain.entities import Load, LoadStatus
from src.core.domain.value_objects import EquipmentType, Rate


class LoadSearchCriteria:
    """Search criteria for loads."""

    def __init__(self,
                 equipment_type: Optional[EquipmentType] = None,
                 origin_state: Optional[str] = None,
                 destination_state: Optional[str] = None,
                 pickup_date_start: Optional[date] = None,
                 pickup_date_end: Optional[date] = None,
                 minimum_rate: Optional[Rate] = None,
                 maximum_rate: Optional[Rate] = None,
                 maximum_miles: Optional[int] = None,
                 weight_min: Optional[int] = None,
                 weight_max: Optional[int] = None,
                 status: Optional[LoadStatus] = None,
                 is_active: bool = True,
                 sort_by: Optional[str] = None,
                 limit: int = 10,
                 offset: int = 0):
        self.equipment_type = equipment_type
        self.origin_state = origin_state
        self.destination_state = destination_state
        self.pickup_date_start = pickup_date_start
        self.pickup_date_end = pickup_date_end
        self.minimum_rate = minimum_rate
        self.maximum_rate = maximum_rate
        self.maximum_miles = maximum_miles
        self.weight_min = weight_min
        self.weight_max = weight_max
        self.status = status
        self.is_active = is_active
        self.sort_by = sort_by
        self.limit = limit
        self.offset = offset


class ILoadRepository(ABC):
    """Port interface for load repository."""

    @abstractmethod
    async def create(self, load: Load) -> Load:
        """Create a new load."""
        pass

    @abstractmethod
    async def get_by_id(self, load_id: UUID) -> Optional[Load]:
        """Get load by ID."""
        pass

    @abstractmethod
    async def get_by_reference_number(self, reference_number: str) -> Optional[Load]:
        """Get load by reference number."""
        pass

    @abstractmethod
    async def update(self, load: Load) -> Load:
        """Update existing load."""
        pass

    @abstractmethod
    async def delete(self, load_id: UUID) -> bool:
        """Delete load (soft delete)."""
        pass

    @abstractmethod
    async def search_loads(self, criteria: LoadSearchCriteria) -> List[Load]:
        """Search loads by criteria."""
        pass

    @abstractmethod
    async def get_available_loads(self, limit: int = 100, offset: int = 0) -> List[Load]:
        """Get list of available loads."""
        pass

    @abstractmethod
    async def get_loads_by_status(self, status: LoadStatus, limit: int = 100, offset: int = 0) -> List[Load]:
        """Get loads by status."""
        pass

    @abstractmethod
    async def get_loads_by_carrier(self, carrier_id: UUID, limit: int = 100, offset: int = 0) -> List[Load]:
        """Get loads booked by specific carrier."""
        pass

    @abstractmethod
    async def count_loads_by_criteria(self, criteria: LoadSearchCriteria) -> int:
        """Count loads matching criteria."""
        pass

    @abstractmethod
    async def get_loads_expiring_soon(self, hours: int = 24) -> List[Load]:
        """Get loads expiring within specified hours."""
        pass

    @abstractmethod
    async def get_load_metrics(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get aggregated load metrics for date range."""
        pass
