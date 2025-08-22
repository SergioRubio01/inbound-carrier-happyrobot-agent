"""
File: update_load_use_case.py
Description: Use case for updating existing loads
Author: HappyRobot Team
Created: 2024-08-20
"""

from dataclasses import dataclass
from datetime import datetime, time
from typing import Dict, List, Optional
from uuid import UUID

from src.config.settings import settings
from src.core.domain.entities import Load, LoadStatus
from src.core.domain.exceptions.base import DomainException
from src.core.domain.value_objects import EquipmentType, Location, Rate
from src.core.ports.repositories import ILoadRepository


class LoadNotFoundException(DomainException):
    """Exception raised when load is not found."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class LoadUpdateException(DomainException):
    """Exception raised when load update fails."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


@dataclass
class UpdateLoadRequest:
    """Request for updating an existing load."""

    load_id: UUID
    origin: Optional[Location] = None
    destination: Optional[Location] = None
    pickup_datetime: Optional[datetime] = None
    delivery_datetime: Optional[datetime] = None
    equipment_type: Optional[str] = None
    loadboard_rate: Optional[float] = None
    weight: Optional[int] = None
    commodity_type: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    dimensions: Optional[str] = None
    num_of_pieces: Optional[int] = None
    miles: Optional[str] = None
    booked: Optional[bool] = None
    session_id: Optional[str] = None


@dataclass
class UpdateLoadResponse:
    """Response for load update."""

    load_id: str
    reference_number: Optional[str]
    status: str
    updated_at: datetime


class UpdateLoadUseCase:
    """Use case for updating existing loads."""

    def __init__(self, load_repository: ILoadRepository):
        self.load_repository = load_repository

    async def execute(self, request: UpdateLoadRequest) -> UpdateLoadResponse:
        """Execute load update."""
        try:
            # Get the existing load
            load = await self.load_repository.get_active_by_id(request.load_id)
            if not load:
                raise LoadNotFoundException(f"Load with ID {request.load_id} not found")

            # Validate business rules before making changes
            await self._validate_update_rules(load, request)

            # Update the load with new values
            updated_load = await self._apply_updates(load, request)

            # Validate the updated load
            await self._validate_updated_load(updated_load, request)

            # Save to repository
            saved_load = await self.load_repository.update(updated_load)

            return UpdateLoadResponse(
                load_id=str(saved_load.load_id),
                reference_number=saved_load.reference_number,
                status=saved_load.status.value,
                updated_at=saved_load.updated_at,
            )

        except (LoadNotFoundException, LoadUpdateException):
            raise
        except Exception as e:
            raise LoadUpdateException(f"Failed to update load: {str(e)}")

    async def _validate_update_rules(
        self, load: Load, request: UpdateLoadRequest
    ) -> None:
        """Validate business rules for load update."""
        # Cannot update delivered loads
        if load.status == LoadStatus.DELIVERED:
            raise LoadUpdateException(
                f"Cannot update load {load.reference_number} - load has been delivered"
            )

        # Validate status transitions if status is being changed
        if request.status and request.status != load.status.value:
            new_status = LoadStatus(request.status)
            if not self._is_valid_status_transition(load.status, new_status):
                raise LoadUpdateException(
                    f"Invalid status transition from {load.status.value} to {new_status.value}"
                )

    def _is_valid_status_transition(
        self, current_status: LoadStatus, new_status: LoadStatus
    ) -> bool:
        """Check if status transition is valid."""
        valid_transitions: Dict[LoadStatus, List[LoadStatus]] = {
            LoadStatus.AVAILABLE: [
                LoadStatus.PENDING,
                LoadStatus.BOOKED,
                LoadStatus.CANCELLED,
            ],
            LoadStatus.PENDING: [
                LoadStatus.AVAILABLE,
                LoadStatus.BOOKED,
                LoadStatus.CANCELLED,
            ],
            LoadStatus.BOOKED: [LoadStatus.IN_TRANSIT, LoadStatus.CANCELLED],
            LoadStatus.IN_TRANSIT: [LoadStatus.DELIVERED],
            LoadStatus.CANCELLED: [],  # Cannot change from cancelled
            LoadStatus.DELIVERED: [],  # Cannot change from delivered
        }

        return new_status in valid_transitions.get(current_status, [])

    async def _apply_updates(self, load: Load, request: UpdateLoadRequest) -> Load:
        """Apply updates to the load entity."""
        # Update location information
        if request.origin:
            load.origin = request.origin

        if request.destination:
            load.destination = request.destination

        # Update schedule information
        if request.pickup_datetime:
            load.pickup_date = request.pickup_datetime.date()
            load.pickup_time_start = request.pickup_datetime.time()

        if request.delivery_datetime:
            load.delivery_date = request.delivery_datetime.date()
            load.delivery_time_start = request.delivery_datetime.time()

        # Update equipment and load details
        if request.equipment_type:
            load.equipment_type = EquipmentType.from_name(request.equipment_type)

        if request.weight is not None:
            load.weight = request.weight

        if request.commodity_type:
            load.commodity_type = request.commodity_type

        # Update pricing information
        if request.loadboard_rate is not None:
            load.loadboard_rate = Rate.from_float(request.loadboard_rate)

        # Update notes
        if request.notes is not None:
            load.notes = request.notes

        # Update new fields
        if request.dimensions is not None:
            load.dimensions = request.dimensions

        if request.num_of_pieces is not None:
            load.num_of_pieces = request.num_of_pieces

        if request.miles is not None:
            load.miles = request.miles

        if request.booked is not None:
            load.booked = request.booked

        if request.session_id is not None:
            load.session_id = request.session_id

        # Update status
        if request.status:
            new_status = LoadStatus(request.status)
            if load.status != new_status:
                load.update_status(new_status)

        # Always update the timestamp
        load.updated_at = datetime.utcnow()

        return load

    async def _validate_updated_load(
        self, load: Load, request: UpdateLoadRequest
    ) -> None:
        """Validate the updated load entity."""
        # Validate required fields are still present
        if not load.origin or not load.destination:
            raise LoadUpdateException("Origin and destination are required")

        if not load.pickup_date or not load.delivery_date:
            raise LoadUpdateException("Pickup and delivery dates are required")

        if not load.equipment_type:
            raise LoadUpdateException("Equipment type is required")

        if not load.loadboard_rate or load.loadboard_rate.to_float() <= 0:
            raise LoadUpdateException("Loadboard rate must be greater than 0")

        if load.weight is None or load.weight <= 0:
            raise LoadUpdateException("Weight must be greater than 0")

        if not load.commodity_type:
            raise LoadUpdateException("Commodity type is required")

        # Validate date logic
        pickup_datetime = datetime.combine(
            load.pickup_date, load.pickup_time_start or time.min
        )
        delivery_datetime = datetime.combine(
            load.delivery_date, load.delivery_time_start or time.min
        )

        if pickup_datetime >= delivery_datetime:
            raise LoadUpdateException(
                "Pickup datetime must be before delivery datetime"
            )

        # Validate weight limits
        if load.weight > settings.max_load_weight_lbs:
            raise LoadUpdateException(
                f"Weight cannot exceed {settings.max_load_weight_lbs:,} pounds"
            )
