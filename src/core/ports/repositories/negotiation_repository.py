"""
File: negotiation_repository.py
Description: Negotiation repository port interface
Author: HappyRobot Team
Created: 2024-08-14
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from src.core.domain.entities import Negotiation, NegotiationStatus
from src.core.domain.value_objects import MCNumber


class NegotiationSearchCriteria:
    """Search criteria for negotiations."""

    def __init__(self,
                 call_id: Optional[UUID] = None,
                 load_id: Optional[UUID] = None,
                 carrier_id: Optional[UUID] = None,
                 mc_number: Optional[MCNumber] = None,
                 session_id: Optional[str] = None,
                 is_active: Optional[bool] = None,
                 final_status: Optional[NegotiationStatus] = None,
                 start_date: Optional[datetime] = None,
                 end_date: Optional[datetime] = None,
                 limit: int = 100,
                 offset: int = 0):
        self.call_id = call_id
        self.load_id = load_id
        self.carrier_id = carrier_id
        self.mc_number = mc_number
        self.session_id = session_id
        self.is_active = is_active
        self.final_status = final_status
        self.start_date = start_date
        self.end_date = end_date
        self.limit = limit
        self.offset = offset


class INegotiationRepository(ABC):
    """Port interface for negotiation repository."""

    @abstractmethod
    async def create(self, negotiation: Negotiation) -> Negotiation:
        """Create a new negotiation."""
        pass

    @abstractmethod
    async def get_by_id(self, negotiation_id: UUID) -> Optional[Negotiation]:
        """Get negotiation by ID."""
        pass

    @abstractmethod
    async def get_by_session_id(self, session_id: str) -> Optional[Negotiation]:
        """Get active negotiation by session ID."""
        pass

    @abstractmethod
    async def update(self, negotiation: Negotiation) -> Negotiation:
        """Update existing negotiation."""
        pass

    @abstractmethod
    async def delete(self, negotiation_id: UUID) -> bool:
        """Delete negotiation."""
        pass

    @abstractmethod
    async def search_negotiations(self, criteria: NegotiationSearchCriteria) -> List[Negotiation]:
        """Search negotiations by criteria."""
        pass

    @abstractmethod
    async def get_negotiations_by_call(self, call_id: UUID) -> List[Negotiation]:
        """Get all negotiations for a specific call."""
        pass

    @abstractmethod
    async def get_negotiations_by_load(self, load_id: UUID, limit: int = 100, offset: int = 0) -> List[Negotiation]:
        """Get negotiations for a specific load."""
        pass

    @abstractmethod
    async def get_active_negotiations(self, limit: int = 100, offset: int = 0) -> List[Negotiation]:
        """Get currently active negotiations."""
        pass

    @abstractmethod
    async def get_negotiations_by_status(self, status: NegotiationStatus, limit: int = 100, offset: int = 0) -> List[Negotiation]:
        """Get negotiations by final status."""
        pass

    @abstractmethod
    async def get_negotiation_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get aggregated negotiation metrics for date range."""
        pass

    @abstractmethod
    async def count_negotiations_by_criteria(self, criteria: NegotiationSearchCriteria) -> int:
        """Count negotiations matching criteria."""
        pass

    @abstractmethod
    async def get_carrier_negotiation_history(self, carrier_id: UUID, limit: int = 50) -> List[Negotiation]:
        """Get negotiation history for a specific carrier."""
        pass
