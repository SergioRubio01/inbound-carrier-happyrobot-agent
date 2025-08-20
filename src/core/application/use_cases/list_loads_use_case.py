"""
File: list_loads_use_case.py
Description: Use case for listing loads with pagination and filtering
Author: HappyRobot Team
Created: 2024-08-20
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime, date

from src.core.domain.entities import Load, LoadStatus
from src.core.ports.repositories import ILoadRepository
from src.core.domain.exceptions.base import DomainException


class LoadListException(DomainException):
    """Exception raised when load listing fails."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


@dataclass
class ListLoadsRequest:
    """Request for listing loads."""
    status: Optional[str] = None
    equipment_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    page: int = 1
    limit: int = 20
    sort_by: str = "created_at_desc"


@dataclass
class LoadSummary:
    """Load summary for list response."""
    load_id: str
    origin: str
    destination: str
    pickup_datetime: datetime
    delivery_datetime: datetime
    equipment_type: str
    loadboard_rate: float
    notes: Optional[str]
    weight: int
    commodity_type: str
    status: str
    created_at: datetime


@dataclass
class ListLoadsResponse:
    """Response for load listing."""
    loads: List[LoadSummary]
    total_count: int
    page: int
    limit: int
    has_next: bool
    has_previous: bool


class ListLoadsUseCase:
    """Use case for listing loads with pagination and filtering."""

    def __init__(self, load_repository: ILoadRepository):
        self.load_repository = load_repository

    async def execute(self, request: ListLoadsRequest) -> ListLoadsResponse:
        """Execute load listing."""
        try:
            # Validate request
            self._validate_request(request)

            # Calculate offset from page
            offset = (request.page - 1) * request.limit

            # Convert status string to enum if provided
            status_enum = None
            if request.status:
                try:
                    status_enum = LoadStatus(request.status.upper())
                except ValueError:
                    raise LoadListException(f"Invalid status: {request.status}")

            # Get loads from repository
            loads, total_count = await self.load_repository.list_all(
                status=status_enum,
                equipment_type=request.equipment_type,
                start_date=request.start_date,
                end_date=request.end_date,
                limit=request.limit,
                offset=offset,
                sort_by=request.sort_by
            )

            # Convert to load summaries
            load_summaries = [self._load_to_summary(load) for load in loads]

            # Calculate pagination info
            has_next = offset + request.limit < total_count
            has_previous = request.page > 1

            return ListLoadsResponse(
                loads=load_summaries,
                total_count=total_count,
                page=request.page,
                limit=request.limit,
                has_next=has_next,
                has_previous=has_previous
            )

        except Exception as e:
            raise LoadListException(f"Failed to list loads: {str(e)}")

    def _validate_request(self, request: ListLoadsRequest) -> None:
        """Validate list loads request."""
        if request.page < 1:
            raise LoadListException("Page must be greater than 0")

        if request.limit < 1 or request.limit > 100:
            raise LoadListException("Limit must be between 1 and 100")

        if request.start_date and request.end_date:
            if request.start_date > request.end_date:
                raise LoadListException("Start date must be before end date")

        # Validate sort_by options
        valid_sorts = [
            "created_at_desc", "created_at_asc",
            "pickup_date_desc", "pickup_date_asc",
            "rate_desc", "rate_asc",
            "rate_per_mile_desc", "rate_per_mile_asc"
        ]

        if request.sort_by not in valid_sorts:
            raise LoadListException(f"Invalid sort_by value. Valid options: {', '.join(valid_sorts)}")

    def _load_to_summary(self, load: Load) -> LoadSummary:
        """Convert load entity to summary for response."""
        # Combine date and time for datetime fields
        pickup_datetime = datetime.combine(
            load.pickup_date,
            load.pickup_time_start or datetime.min.time()
        )

        delivery_datetime = datetime.combine(
            load.delivery_date,
            load.delivery_time_start or datetime.min.time()
        )

        return LoadSummary(
            load_id=str(load.load_id),
            origin=f"{load.origin.city}, {load.origin.state}",
            destination=f"{load.destination.city}, {load.destination.state}",
            pickup_datetime=pickup_datetime,
            delivery_datetime=delivery_datetime,
            equipment_type=load.equipment_type.name,
            loadboard_rate=load.loadboard_rate.to_float(),
            notes=load.notes,
            weight=load.weight,
            commodity_type=load.commodity_type,
            status=load.status.value,
            created_at=load.created_at
        )
