"""
File: load_model.py
Description: SQLAlchemy model for load information
Author: HappyRobot Team
Created: 2024-08-14
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Column,
    Date,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, NUMERIC, UUID
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from src.infrastructure.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from .carrier_model import CarrierModel


class LoadModel(Base, TimestampMixin):
    """SQLAlchemy model for loads table."""

    __tablename__ = "loads"

    # Primary Key
    load_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Load Reference
    reference_number = Column(String(50), unique=True, index=True)
    external_id = Column(String(100))  # ID from external system

    # Origin Information
    origin_city = Column(String(100), nullable=False, index=True)
    origin_state = Column(String(2), nullable=False, index=True)
    origin_zip = Column(String(10))
    origin_coordinates = Column(JSONB)  # {lat, lng}
    origin_facility = Column(JSONB)  # {name, address, contact, hours}

    # Destination Information
    destination_city = Column(String(100), nullable=False, index=True)
    destination_state = Column(String(2), nullable=False, index=True)
    destination_zip = Column(String(10))
    destination_coordinates = Column(JSONB)  # {lat, lng}
    destination_facility = Column(JSONB)  # {name, address, contact, hours}

    # Schedule
    pickup_date = Column(Date, nullable=False, index=True)
    pickup_time_start = Column(Time)
    pickup_time_end = Column(Time)
    pickup_appointment_required = Column(Boolean, default=False)

    delivery_date = Column(Date, nullable=False)
    delivery_time_start = Column(Time)
    delivery_time_end = Column(Time)
    delivery_appointment_required = Column(Boolean, default=False)

    # Equipment Requirements
    equipment_type = Column(String(50), nullable=False, index=True)
    equipment_requirements = Column(JSONB)  # {tarps, straps, temp_control, etc}

    # Load Details
    weight = Column(Integer, nullable=False)  # in pounds
    pieces = Column(Integer)
    commodity_type = Column(String(100))
    commodity_description = Column(Text)
    dimensions = Column(String(100))  # LxWxH
    hazmat = Column(Boolean, default=False)
    hazmat_class = Column(String(20))

    # Distance and Route
    miles = Column(Integer, nullable=False, index=True)
    estimated_transit_hours = Column(Integer)
    route_notes = Column(Text)

    # Pricing
    loadboard_rate = Column(NUMERIC(10, 2), nullable=False, index=True)
    fuel_surcharge = Column(NUMERIC(10, 2), default=0)
    accessorials = Column(JSONB)  # [{type, amount, description}]

    # Negotiation Parameters
    minimum_rate = Column(NUMERIC(10, 2))
    maximum_rate = Column(NUMERIC(10, 2))
    target_rate = Column(NUMERIC(10, 2))
    auto_accept_threshold = Column(NUMERIC(10, 2))

    # Broker/Customer Information
    broker_company = Column(String(255))
    broker_contact = Column(JSONB)  # {name, phone, email}
    customer_name = Column(String(255))

    # Status
    status = Column(String(30), nullable=False, default="AVAILABLE", index=True)
    # AVAILABLE, PENDING, BOOKED, IN_TRANSIT, DELIVERED, CANCELLED
    status_changed_at = Column(TIMESTAMP(timezone=True), default=func.now())
    booked_by_carrier_id = Column(UUID(as_uuid=True), ForeignKey("carriers.carrier_id"))
    booked_at = Column(TIMESTAMP(timezone=True))

    # Special Instructions
    special_requirements = Column(ARRAY(Text))
    notes = Column(Text)
    internal_notes = Column(Text)  # Not shown to carriers

    # Urgency and Priority
    urgency = Column(String(20), default="NORMAL")  # LOW, NORMAL, HIGH, CRITICAL
    priority_score = Column(Integer, default=50)  # 0-100

    # Visibility
    is_active = Column(Boolean, default=True, index=True)
    expires_at = Column(TIMESTAMP(timezone=True))

    # Metadata
    source = Column(String(50))  # DAT, MANUAL, API, etc.
    created_by = Column(String(100))
    deleted_at = Column(TIMESTAMP(timezone=True))
    version = Column(Integer, default=1)

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
