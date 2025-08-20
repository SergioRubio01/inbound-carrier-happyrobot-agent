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
    external_id: Optional[str] = None

    # Location Information
    origin: Location = field(default=None)
    destination: Location = field(default=None)

    # Schedule
    pickup_date: date = field(default=None)
    pickup_time_start: Optional[time] = None
    pickup_time_end: Optional[time] = None
    pickup_appointment_required: bool = False

    delivery_date: date = field(default=None)
    delivery_time_start: Optional[time] = None
    delivery_time_end: Optional[time] = None
    delivery_appointment_required: bool = False

    # Equipment Requirements
    equipment_type: EquipmentType = field(default=None)
    equipment_requirements: Optional[Dict[str, Any]] = None

    # Load Details
    weight: int = 0  # in pounds
    pieces: Optional[int] = None
    commodity_type: Optional[str] = None
    commodity_description: Optional[str] = None
    dimensions: Optional[str] = None
    hazmat: bool = False
    hazmat_class: Optional[str] = None

    # Distance and Route
    miles: int = 0
    estimated_transit_hours: Optional[int] = None
    route_notes: Optional[str] = None

    # Pricing
    loadboard_rate: Rate = field(default=None)
    fuel_surcharge: Optional[Rate] = None
    accessorials: Optional[List[Dict[str, Any]]] = None

    # Negotiation Parameters
    minimum_rate: Optional[Rate] = None
    maximum_rate: Optional[Rate] = None
    target_rate: Optional[Rate] = None
    auto_accept_threshold: Optional[Rate] = None

    # Broker/Customer Information
    broker_company: Optional[str] = None
    broker_contact: Optional[Dict[str, Any]] = None
    customer_name: Optional[str] = None

    # Status
    status: LoadStatus = LoadStatus.AVAILABLE
    status_changed_at: datetime = field(default_factory=datetime.utcnow)
    booked_by_carrier_id: Optional[UUID] = None
    booked_at: Optional[datetime] = None

    # Special Instructions
    special_requirements: Optional[List[str]] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None

    # Urgency and Priority
    urgency: UrgencyLevel = UrgencyLevel.NORMAL
    priority_score: int = 50  # 0-100

    # Visibility
    is_active: bool = True
    expires_at: Optional[datetime] = None

    # Metadata
    source: Optional[str] = None  # DAT, MANUAL, API, etc.
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    deleted_at: Optional[datetime] = None
    version: int = 1

    @property
    def total_rate(self) -> Rate:
        """Calculate total rate including fuel surcharge."""
        if self.fuel_surcharge:
            return self.loadboard_rate.add(self.fuel_surcharge)
        return self.loadboard_rate

    @property
    def rate_per_mile(self) -> Rate:
        """Calculate rate per mile."""
        if self.miles and self.miles > 0:
            return self.total_rate.divide(self.miles)
        return Rate.from_float(0)

    @property
    def lane_key(self) -> str:
        """Get lane key for rate history."""
        return f"{self.origin.state}-{self.destination.state}"

    @property
    def is_available(self) -> bool:
        """Check if load is available for booking."""
        return (
            self.status == LoadStatus.AVAILABLE
            and self.is_active
            and (self.expires_at is None or self.expires_at > datetime.utcnow())
            and self.deleted_at is None
        )

    def verify_availability(self) -> None:
        """Verify load availability and raise exception if not available."""
        if not self.is_available:
            if self.status != LoadStatus.AVAILABLE:
                raise LoadNotAvailableException(
                    f"Load {self.reference_number} status is {self.status.value}"
                )

            if not self.is_active:
                raise LoadNotAvailableException(
                    f"Load {self.reference_number} is not active"
                )

            if self.expires_at and self.expires_at <= datetime.utcnow():
                raise LoadNotAvailableException(
                    f"Load {self.reference_number} has expired"
                )

            if self.deleted_at:
                raise LoadNotAvailableException(
                    f"Load {self.reference_number} has been deleted"
                )

    def book_by_carrier(
        self, carrier_id: UUID, agreed_rate: Optional[Rate] = None
    ) -> None:
        """Book the load by a carrier."""
        self.verify_availability()

        self.status = LoadStatus.BOOKED
        self.status_changed_at = datetime.utcnow()
        self.booked_by_carrier_id = carrier_id
        self.booked_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

        # Update the loadboard rate if a different rate was agreed upon
        if agreed_rate and agreed_rate != self.loadboard_rate:
            self.loadboard_rate = agreed_rate

    def cancel_booking(self, reason: Optional[str] = None) -> None:
        """Cancel the load booking."""
        self.status = LoadStatus.CANCELLED
        self.status_changed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

        if reason and self.internal_notes:
            self.internal_notes += f" | Cancelled: {reason}"
        elif reason:
            self.internal_notes = f"Cancelled: {reason}"

    def update_status(self, new_status: LoadStatus) -> None:
        """Update load status."""
        if self.status != new_status:
            self.status = new_status
            self.status_changed_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()

    def matches_equipment(self, equipment_type: EquipmentType) -> bool:
        """Check if load matches the given equipment type."""
        return self.equipment_type.name.lower() == equipment_type.name.lower()

    def matches_weight_capacity(self, equipment_type: EquipmentType) -> bool:
        """Check if equipment can handle the load weight."""
        return equipment_type.can_haul_weight(self.weight)

    def calculate_negotiation_thresholds(
        self, urgency_factor: float = 1.0, history_factor: float = 1.0
    ) -> Dict[str, Rate]:
        """Calculate negotiation thresholds based on various factors."""
        base_rate = self.loadboard_rate

        # Calculate thresholds
        min_rate = base_rate.multiply(0.95)  # 5% below
        max_rate = base_rate.multiply(urgency_factor * history_factor)
        auto_accept = base_rate.multiply(1.02)  # 2% above

        return {
            "minimum_rate": min_rate,
            "maximum_rate": max_rate,
            "auto_accept_threshold": auto_accept,
            "loadboard_rate": base_rate,
        }

    def __eq__(self, other) -> bool:
        if isinstance(other, Load):
            return self.load_id == other.load_id
        return False

    def __hash__(self) -> int:
        return hash(self.load_id)

    def __str__(self) -> str:
        return f"Load(reference={self.reference_number}, origin='{self.origin}', destination='{self.destination}')"
