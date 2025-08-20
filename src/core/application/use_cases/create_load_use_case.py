"""
File: create_load_use_case.py
Description: Use case for creating new loads
Author: HappyRobot Team
Created: 2024-08-20
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime, date, time
from uuid import uuid4

from src.core.domain.entities import Load, LoadStatus, UrgencyLevel
from src.core.domain.value_objects import Location, EquipmentType, Rate
from src.core.ports.repositories import ILoadRepository
from src.core.domain.exceptions.base import DomainException
from src.config.settings import settings


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
    reference_number: Optional[str] = None
    broker_company: Optional[str] = None
    special_requirements: Optional[List[str]] = None
    customer_name: Optional[str] = None
    dimensions: Optional[str] = None
    pieces: Optional[int] = None
    hazmat: bool = False
    hazmat_class: Optional[str] = None
    miles: Optional[int] = None
    fuel_surcharge: Optional[float] = None
    source: str = "API"


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

            # Generate reference number if not provided
            reference_number = request.reference_number
            if not reference_number:
                reference_number = await self._generate_reference_number()
            else:
                # Check for duplicate reference numbers
                existing_load = await self.load_repository.get_by_reference_number(reference_number)
                if existing_load:
                    raise DuplicateReferenceException(f"Load with reference number '{reference_number}' already exists")

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
                broker_company=request.broker_company,
                special_requirements=request.special_requirements,
                customer_name=request.customer_name,
                dimensions=request.dimensions,
                pieces=request.pieces,
                hazmat=request.hazmat,
                hazmat_class=request.hazmat_class,
                miles=request.miles or self._calculate_estimated_miles(request.origin, request.destination),
                fuel_surcharge=Rate.from_float(request.fuel_surcharge) if request.fuel_surcharge else None,
                status=LoadStatus.AVAILABLE,
                urgency=UrgencyLevel.NORMAL,
                is_active=True,
                source=request.source,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            # Save to repository
            created_load = await self.load_repository.create(load)

            return CreateLoadResponse(
                load_id=str(created_load.load_id),
                reference_number=created_load.reference_number,
                status=created_load.status.value,
                created_at=created_load.created_at
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
            raise LoadCreationException("Pickup datetime must be before delivery datetime")

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
            raise LoadCreationException(f"Invalid equipment type: {request.equipment_type}")

        # Validate rate
        try:
            Rate.from_float(request.loadboard_rate)
        except Exception:
            raise LoadCreationException(f"Invalid loadboard rate: {request.loadboard_rate}")

        # Validate fuel surcharge if provided
        if request.fuel_surcharge is not None:
            try:
                Rate.from_float(request.fuel_surcharge)
            except Exception:
                raise LoadCreationException(f"Invalid fuel surcharge: {request.fuel_surcharge}")

        # Validate weight limits
        if request.weight > settings.max_load_weight_lbs:
            raise LoadCreationException(f"Weight cannot exceed {settings.max_load_weight_lbs:,} pounds")

        # Validate hazmat fields
        if request.hazmat and not request.hazmat_class:
            raise LoadCreationException("Hazmat class is required when load is hazmat")

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
                raise LoadCreationException("Unable to generate unique reference number")

    def _calculate_estimated_miles(self, origin: Location, destination: Location) -> int:
        """Calculate estimated miles between origin and destination."""
        # If coordinates are available, calculate actual distance
        distance = origin.distance_to(destination)
        if distance:
            return int(distance)

        # Fallback: estimate based on state-to-state averages
        state_distances = {
            ("CA", "NY"): 2900, ("CA", "FL"): 2750, ("CA", "TX"): 1400,
            ("TX", "NY"): 1600, ("TX", "FL"): 1200, ("FL", "NY"): 1100,
            # Add more state pairs as needed
        }

        state_pair = (origin.state, destination.state)
        reverse_pair = (destination.state, origin.state)

        if state_pair in state_distances:
            return state_distances[state_pair]
        elif reverse_pair in state_distances:
            return state_distances[reverse_pair]

        # Default estimate for unknown routes
        return 1000
