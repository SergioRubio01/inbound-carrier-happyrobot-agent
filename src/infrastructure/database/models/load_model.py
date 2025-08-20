"""
File: load_model.py
Description: SQLAlchemy model for load information
Author: HappyRobot Team
Created: 2024-08-14
"""

import uuid
from datetime import date, datetime, time
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import TIMESTAMP, Boolean, Date, ForeignKey, Integer, String, Text, Time
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, NUMERIC, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.infrastructure.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from .carrier_model import CarrierModel


class LoadModel(Base, TimestampMixin):
    """SQLAlchemy model for loads table."""

    __tablename__ = "loads"

    # Primary Key
    load_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Load Reference
    reference_number: Mapped[Optional[str]] = mapped_column(
        String(50), unique=True, index=True, nullable=True
    )
    external_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # ID from external system

    # Origin Information
    origin_city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    origin_state: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    origin_zip: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    origin_coordinates: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )  # {lat, lng}
    origin_facility: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )  # {name, address, contact, hours}

    # Destination Information
    destination_city: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    destination_state: Mapped[str] = mapped_column(
        String(2), nullable=False, index=True
    )
    destination_zip: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    destination_coordinates: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )  # {lat, lng}
    destination_facility: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )  # {name, address, contact, hours}

    # Schedule
    pickup_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    pickup_time_start: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    pickup_time_end: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    pickup_appointment_required: Mapped[bool] = mapped_column(Boolean, default=False)

    delivery_date: Mapped[date] = mapped_column(Date, nullable=False)
    delivery_time_start: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    delivery_time_end: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    delivery_appointment_required: Mapped[bool] = mapped_column(Boolean, default=False)

    # Equipment Requirements
    equipment_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    equipment_requirements: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )  # {tarps, straps, temp_control, etc}

    # Load Details
    weight: Mapped[int] = mapped_column(Integer, nullable=False)  # in pounds
    pieces: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    commodity_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    commodity_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dimensions: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # LxWxH
    hazmat: Mapped[bool] = mapped_column(Boolean, default=False)
    hazmat_class: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Distance and Route
    miles: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    estimated_transit_hours: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    route_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Pricing
    loadboard_rate: Mapped[float] = mapped_column(
        NUMERIC(10, 2), nullable=False, index=True
    )
    fuel_surcharge: Mapped[float] = mapped_column(NUMERIC(10, 2), default=0)
    accessorials: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )  # [{type, amount, description}]

    # Negotiation Parameters
    minimum_rate: Mapped[Optional[float]] = mapped_column(NUMERIC(10, 2), nullable=True)
    maximum_rate: Mapped[Optional[float]] = mapped_column(NUMERIC(10, 2), nullable=True)
    target_rate: Mapped[Optional[float]] = mapped_column(NUMERIC(10, 2), nullable=True)
    auto_accept_threshold: Mapped[Optional[float]] = mapped_column(
        NUMERIC(10, 2), nullable=True
    )

    # Broker/Customer Information
    broker_company: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    broker_contact: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )  # {name, phone, email}
    customer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="AVAILABLE", index=True
    )
    # AVAILABLE, PENDING, BOOKED, IN_TRANSIT, DELIVERED, CANCELLED
    status_changed_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=func.now()
    )
    booked_by_carrier_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("carriers.carrier_id"), nullable=True
    )
    booked_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )

    # Special Instructions
    special_requirements: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(Text), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Not shown to carriers

    # Urgency and Priority
    urgency: Mapped[str] = mapped_column(
        String(20), default="NORMAL"
    )  # LOW, NORMAL, HIGH, CRITICAL
    priority_score: Mapped[int] = mapped_column(Integer, default=50)  # 0-100

    # Visibility
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )

    # Metadata
    source: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # DAT, MANUAL, API, etc.
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Relationships
    booked_by_carrier: Mapped["CarrierModel"] = relationship(
        "CarrierModel", foreign_keys=[booked_by_carrier_id]
    )

    @property
    def total_rate(self) -> float:
        """Calculate total rate including fuel surcharge."""
        return float(self.loadboard_rate) + float(self.fuel_surcharge or 0)

    @property
    def rate_per_mile(self) -> float:
        """Calculate rate per mile."""
        if self.miles and self.miles > 0:
            return float(self.total_rate / self.miles)
        return 0.0

    def __repr__(self) -> str:
        return f"<LoadModel(reference_number='{self.reference_number}', origin='{self.origin_city}, {self.origin_state}', destination='{self.destination_city}, {self.destination_state}')>"
