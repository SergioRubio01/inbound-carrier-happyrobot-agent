"""
File: load.py
Description: Load domain entity
Author: HappyRobot Team
Created: 2024-08-14
"""

from dataclasses import dataclass, field
from datetime import datetime, date, time
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from enum import Enum

from ..value_objects import Rate, Location, EquipmentType
from ..exceptions.base import DomainException


class LoadNotAvailableException(DomainException):
    """Exception raised when load is not available."""
    pass


class LoadStatus(Enum):
    """Load status enumeration."""
    AVAILABLE = "AVAILABLE"
    PENDING = "PENDING"
    BOOKED = "BOOKED"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class UrgencyLevel(Enum):
    """Load urgency level enumeration."""
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class Load:
    """Domain entity for loads."""

    # Identity
    load_id: UUID = field(default_factory=uuid4)
    reference_number: Optional[str] = None

    # Location Information
    origin: Location = field(default=None)
    destination: Location = field(default=None)

    # Schedule
    pickup_date: date = field(default=None)
    pickup_time_start: Optional[time] = None
    delivery_date: date = field(default=None)
    delivery_time_start: Optional[time] = None

    # Equipment Requirements
    equipment_type: EquipmentType = field(default=None)

    # Load Details
    weight: int = 0  # in pounds
    commodity_type: Optional[str] = None

    # Pricing
    loadboard_rate: Rate = field(default=None)

    # Status
    status: LoadStatus = LoadStatus.AVAILABLE

    # Special Instructions
    notes: Optional[str] = None

    # Visibility
    is_active: bool = True

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1

    @property
    def lane_key(self) -> str:
        """Get lane key for rate history."""
        return f"{self.origin.state}-{self.destination.state}"

    @property
    def is_available(self) -> bool:
        """Check if load is available for booking."""
        return (
            self.status == LoadStatus.AVAILABLE and
            self.is_active
        )

    def verify_availability(self) -> None:
        """Verify load availability and raise exception if not available."""
        if not self.is_available:
            if self.status != LoadStatus.AVAILABLE:
                raise LoadNotAvailableException(f"Load {self.reference_number} status is {self.status.value}")

            if not self.is_active:
                raise LoadNotAvailableException(f"Load {self.reference_number} is not active")

    def book_by_carrier(self, agreed_rate: Optional[Rate] = None) -> None:
        """Book the load by a carrier."""
        self.verify_availability()

        self.status = LoadStatus.BOOKED
        self.updated_at = datetime.utcnow()

        # Update the loadboard rate if a different rate was agreed upon
        if agreed_rate and agreed_rate != self.loadboard_rate:
            self.loadboard_rate = agreed_rate

    def cancel_booking(self, reason: Optional[str] = None) -> None:
        """Cancel the load booking."""
        self.status = LoadStatus.CANCELLED
        self.updated_at = datetime.utcnow()

    def update_status(self, new_status: LoadStatus) -> None:
        """Update load status."""
        if self.status != new_status:
            self.status = new_status
            self.updated_at = datetime.utcnow()

    def matches_equipment(self, equipment_type: EquipmentType) -> bool:
        """Check if load matches the given equipment type."""
        return self.equipment_type.name.lower() == equipment_type.name.lower()

    def matches_weight_capacity(self, equipment_type: EquipmentType) -> bool:
        """Check if equipment can handle the load weight."""
        return equipment_type.can_haul_weight(self.weight)

    def __eq__(self, other) -> bool:
        if isinstance(other, Load):
            return self.load_id == other.load_id
        return False

    def __hash__(self) -> int:
        return hash(self.load_id)

    def __str__(self) -> str:
        return f"Load(reference={self.reference_number}, origin='{self.origin}', destination='{self.destination}')"
