"""
File: update_load_use_case.py
Description: Use case for updating existing loads
Author: HappyRobot Team
Created: 2024-08-20
"""

from dataclasses import dataclass
from datetime import datetime, time
from typing import Optional
from uuid import UUID

from src.config.settings import settings
from src.core.domain.entities import Load
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
    booked: bool
    updated_at: datetime
    # Include all potentially updated fields
    origin: Optional[str] = None  # Formatted as "City, ST"
    destination: Optional[str] = None  # Formatted as "City, ST"
    pickup_datetime: Optional[datetime] = None
    delivery_datetime: Optional[datetime] = None
    equipment_type: Optional[str] = None
    loadboard_rate: Optional[float] = None
    weight: Optional[int] = None
    commodity_type: Optional[str] = None
    notes: Optional[str] = None
    dimensions: Optional[str] = None
    num_of_pieces: Optional[int] = None
    miles: Optional[str] = None
    session_id: Optional[str] = None
    modified_fields: Optional[list] = None  # Track which fields were actually modified


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

            # Track which fields are being modified
            modified_fields = self._track_modified_fields(request)

            # Update the load with new values
            updated_load = await self._apply_updates(load, request)

            # Validate the updated load
            await self._validate_updated_load(updated_load, request)

            # Save to repository
            saved_load = await self.load_repository.update(updated_load)

            # Build comprehensive response including all updated fields
            response = UpdateLoadResponse(
                load_id=str(saved_load.load_id),
                reference_number=saved_load.reference_number,
                booked=saved_load.booked,
                updated_at=saved_load.updated_at,
                modified_fields=modified_fields,
            )

            # Add the actual updated values to the response
            if request.origin and saved_load.origin:
                response.origin = f"{saved_load.origin.city}, {saved_load.origin.state}"
            if request.destination and saved_load.destination:
                response.destination = (
                    f"{saved_load.destination.city}, {saved_load.destination.state}"
                )
            if request.pickup_datetime and saved_load.pickup_date:
                response.pickup_datetime = datetime.combine(
                    saved_load.pickup_date, saved_load.pickup_time_start or time.min
                )
            if request.delivery_datetime and saved_load.delivery_date:
                response.delivery_datetime = datetime.combine(
                    saved_load.delivery_date, saved_load.delivery_time_start or time.min
                )
            if request.equipment_type and saved_load.equipment_type:
                response.equipment_type = saved_load.equipment_type.name
            if request.loadboard_rate is not None and saved_load.loadboard_rate:
                response.loadboard_rate = saved_load.loadboard_rate.to_float()
            if request.weight is not None:
                response.weight = saved_load.weight
            if request.commodity_type:
                response.commodity_type = saved_load.commodity_type
            if request.notes is not None:
                response.notes = saved_load.notes
            if request.dimensions is not None:
                response.dimensions = saved_load.dimensions
            if request.num_of_pieces is not None:
                response.num_of_pieces = saved_load.num_of_pieces
            if request.miles is not None:
                response.miles = saved_load.miles
            if request.session_id is not None:
                response.session_id = saved_load.session_id

            return response

        except (LoadNotFoundException, LoadUpdateException):
            raise
        except Exception as e:
            raise LoadUpdateException(f"Failed to update load: {str(e)}")

    async def _validate_update_rules(
        self, load: Load, request: UpdateLoadRequest
    ) -> None:
        """Validate business rules for load update."""
        # Simplified validation - just check if load is active
        if not load.is_active:
            raise LoadUpdateException(
                f"Cannot update load {load.reference_number} - load is not active"
            )

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

        # Booked status can be updated directly

        # Always update the timestamp
        load.updated_at = datetime.utcnow()

        return load

    def _track_modified_fields(self, request: UpdateLoadRequest) -> list:
        """Track which fields are being modified in the request."""
        modified = []
        if request.origin is not None:
            modified.append("origin")
        if request.destination is not None:
            modified.append("destination")
        if request.pickup_datetime is not None:
            modified.append("pickup_datetime")
        if request.delivery_datetime is not None:
            modified.append("delivery_datetime")
        if request.equipment_type is not None:
            modified.append("equipment_type")
        if request.loadboard_rate is not None:
            modified.append("loadboard_rate")
        if request.weight is not None:
            modified.append("weight")
        if request.commodity_type is not None:
            modified.append("commodity_type")
        if request.notes is not None:
            modified.append("notes")
        if request.dimensions is not None:
            modified.append("dimensions")
        if request.num_of_pieces is not None:
            modified.append("num_of_pieces")
        if request.miles is not None:
            modified.append("miles")
        if request.booked is not None:
            modified.append("booked")
        if request.session_id is not None:
            modified.append("session_id")
        return modified

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
