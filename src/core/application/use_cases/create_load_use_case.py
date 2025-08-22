"""
File: create_load_use_case.py
Description: Use case for creating new loads
Author: HappyRobot Team
Created: 2024-08-20
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import uuid4

from src.config.settings import settings
from src.core.domain.entities import Load, LoadStatus
from src.core.domain.exceptions.base import DomainException
from src.core.domain.value_objects import EquipmentType, Location, Rate
from src.core.ports.repositories import ILoadRepository


class LoadCreationException(DomainException):
    """Exception raised when load creation fails."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class DuplicateReferenceException(DomainException):
    """Exception raised when reference number already exists."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


@dataclass
class CreateLoadRequest:
    """Request for creating a new load."""

    origin: Location
    destination: Location
    pickup_datetime: datetime
    delivery_datetime: datetime
    equipment_type: str
    loadboard_rate: float
    weight: int
    commodity_type: str
    notes: Optional[str] = None
    dimensions: Optional[str] = None
    num_of_pieces: Optional[int] = None
    miles: Optional[str] = None
    booked: Optional[bool] = False
    session_id: Optional[str] = None
    reference_number: Optional[str] = None


@dataclass
class CreateLoadResponse:
    """Response for load creation."""

    load_id: str
    reference_number: str
    status: str
    created_at: datetime


class CreateLoadUseCase:
    """Use case for creating new loads."""

    def __init__(self, load_repository: ILoadRepository):
        self.load_repository = load_repository

    async def execute(self, request: CreateLoadRequest) -> CreateLoadResponse:
        """Execute load creation."""
        try:
            # Validate the request
            await self._validate_request(request)

            # Use custom reference number or generate one
            if request.reference_number:
                reference_number = request.reference_number
                # Check for duplicate reference
                existing_load = await self.load_repository.get_by_reference_number(
                    reference_number
                )
                if existing_load:
                    raise DuplicateReferenceException(
                        f"Reference number {reference_number} already exists"
                    )
            else:
                reference_number = await self._generate_reference_number()

            # Extract date and time components from datetime
            pickup_date = request.pickup_datetime.date()
            pickup_time_start = request.pickup_datetime.time()
            delivery_date = request.delivery_datetime.date()
            delivery_time_start = request.delivery_datetime.time()

            # Create domain entity
            load = Load(
                load_id=uuid4(),
                reference_number=reference_number,
                origin=request.origin,
                destination=request.destination,
                pickup_date=pickup_date,
                pickup_time_start=pickup_time_start,
                delivery_date=delivery_date,
                delivery_time_start=delivery_time_start,
                equipment_type=EquipmentType.from_name(request.equipment_type),
                loadboard_rate=Rate.from_float(request.loadboard_rate),
                weight=request.weight,
                commodity_type=request.commodity_type,
                notes=request.notes,
                dimensions=request.dimensions,
                num_of_pieces=request.num_of_pieces,
                miles=request.miles,
                booked=request.booked or False,
                session_id=request.session_id,
                status=LoadStatus.AVAILABLE,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            # Save to repository
            created_load = await self.load_repository.create(load)

            # Reference number should always be set after creation
            if created_load.reference_number is None:
                raise LoadCreationException("Reference number was not generated")

            return CreateLoadResponse(
                load_id=str(created_load.load_id),
                reference_number=created_load.reference_number,
                status=created_load.status.value,
                created_at=created_load.created_at,
            )

        except DuplicateReferenceException:
            raise
        except Exception as e:
            raise LoadCreationException(f"Failed to create load: {str(e)}")

    async def _validate_request(self, request: CreateLoadRequest) -> None:
        """Validate create load request."""
        # Validate required fields
        if not request.origin:
            raise LoadCreationException("Origin is required")

        if not request.destination:
            raise LoadCreationException("Destination is required")

        if not request.pickup_datetime:
            raise LoadCreationException("Pickup datetime is required")

        if not request.delivery_datetime:
            raise LoadCreationException("Delivery datetime is required")

        if not request.equipment_type:
            raise LoadCreationException("Equipment type is required")

        if request.loadboard_rate is None or request.loadboard_rate <= 0:
            raise LoadCreationException("Loadboard rate must be greater than 0")

        if request.weight is None or request.weight <= 0:
            raise LoadCreationException("Weight must be greater than 0")

        if not request.commodity_type:
            raise LoadCreationException("Commodity type is required")

        # Validate dates
        if request.pickup_datetime >= request.delivery_datetime:
            raise LoadCreationException(
                "Pickup datetime must be before delivery datetime"
            )

        # Make current_time timezone-aware if pickup_datetime is timezone-aware
        if request.pickup_datetime.tzinfo is not None:
            from datetime import timezone

            current_time = datetime.now(timezone.utc)
        else:
            current_time = datetime.utcnow()

        if request.pickup_datetime < current_time:
            raise LoadCreationException("Pickup datetime cannot be in the past")

        # Validate equipment type
        try:
            EquipmentType.from_name(request.equipment_type)
        except Exception:
            raise LoadCreationException(
                f"Invalid equipment type: {request.equipment_type}"
            )

        # Validate rate
        try:
            Rate.from_float(request.loadboard_rate)
        except Exception:
            raise LoadCreationException(
                f"Invalid loadboard rate: {request.loadboard_rate}"
            )

        # Validate weight limits
        if request.weight > settings.max_load_weight_lbs:
            raise LoadCreationException(
                f"Weight cannot exceed {settings.max_load_weight_lbs:,} pounds"
            )

    async def _generate_reference_number(self) -> str:
        """Generate a unique reference number."""
        current_date = datetime.utcnow()
        base_ref = f"LD-{current_date.strftime('%Y-%m')}"

        # Find the next sequential number for this month
        counter = 1
        while True:
            ref_number = f"{base_ref}-{counter:05d}"
            existing = await self.load_repository.get_by_reference_number(ref_number)
            if not existing:
                return ref_number
            counter += 1

            # Prevent infinite loops
            if counter > settings.max_reference_number_counter:
                raise LoadCreationException(
                    "Unable to generate unique reference number"
                )
