"""
File: call_repository.py
Description: Call repository port interface
Author: HappyRobot Team
Created: 2024-08-14
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from src.core.domain.entities import Call, CallOutcome, Sentiment
from src.core.domain.value_objects import MCNumber


class CallSearchCriteria:
    """Search criteria for calls."""

    def __init__(
        self,
        mc_number: Optional[MCNumber] = None,
        carrier_id: Optional[UUID] = None,
        load_id: Optional[UUID] = None,
        outcome: Optional[CallOutcome] = None,
        sentiment: Optional[Sentiment] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transferred_to_human: Optional[bool] = None,
        follow_up_required: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ):
        self.mc_number = mc_number
        self.carrier_id = carrier_id
        self.load_id = load_id
        self.outcome = outcome
        self.sentiment = sentiment
        self.start_date = start_date
        self.end_date = end_date
        self.transferred_to_human = transferred_to_human
        self.follow_up_required = follow_up_required
        self.limit = limit
        self.offset = offset


class ICallRepository(ABC):
    """Port interface for call repository."""

    @abstractmethod
    async def create(self, call: Call) -> Call:
        """Create a new call."""
        pass

    @abstractmethod
    async def get_by_id(self, call_id: UUID) -> Optional[Call]:
        """Get call by ID."""
        pass

    @abstractmethod
    async def get_by_external_id(self, external_call_id: str) -> Optional[Call]:
        """Get call by external call ID."""
        pass

    @abstractmethod
    async def update(self, call: Call) -> Call:
        """Update existing call."""
        pass

    @abstractmethod
    async def delete(self, call_id: UUID) -> bool:
        """Delete call."""
        pass

    @abstractmethod
    async def search_calls(self, criteria: CallSearchCriteria) -> List[Call]:
        """Search calls by criteria."""
        pass

    @abstractmethod
    async def get_calls_by_carrier(
        self, carrier_id: UUID, limit: int = 100, offset: int = 0
    ) -> List[Call]:
        """Get calls by carrier."""
        pass

    @abstractmethod
    async def get_calls_by_outcome(
        self, outcome: CallOutcome, limit: int = 100, offset: int = 0
    ) -> List[Call]:
        """Get calls by outcome."""
        pass

    @abstractmethod
    async def get_calls_requiring_follow_up(
        self, limit: int = 100, offset: int = 0
    ) -> List[Call]:
        """Get calls that require follow-up."""
        pass

    @abstractmethod
    async def get_active_calls(self, limit: int = 100, offset: int = 0) -> List[Call]:
        """Get currently active calls."""
        pass

    @abstractmethod
    async def get_call_metrics(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get aggregated call metrics for date range."""
        pass

    @abstractmethod
    async def count_calls_by_criteria(self, criteria: CallSearchCriteria) -> int:
        """Count calls matching criteria."""
        pass
