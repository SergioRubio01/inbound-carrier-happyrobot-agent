"""
File: load_model.py
Description: SQLAlchemy model for load information
Author: HappyRobot Team
Created: 2024-08-14
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Date, Integer, String, Text, Time
from sqlalchemy.dialects.postgresql import NUMERIC, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    pass


class LoadModel(Base, TimestampMixin):
    """SQLAlchemy model for loads table."""

    __tablename__ = "loads"

    # Primary Key
    load_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Load Reference
    reference_number = Column(String(50), unique=True, index=True)

    # Origin Information
    origin_city = Column(String(100), nullable=False, index=True)
    origin_state = Column(String(2), nullable=False, index=True)
    origin_zip = Column(String(10))

    # Destination Information
    destination_city = Column(String(100), nullable=False, index=True)
    destination_state = Column(String(2), nullable=False, index=True)
    destination_zip = Column(String(10))

    # Schedule
    pickup_date = Column(Date, nullable=False, index=True)
    pickup_time_start = Column(Time)
    delivery_date = Column(Date, nullable=False)
    delivery_time_start = Column(Time)

    # Equipment Requirements
    equipment_type = Column(String(50), nullable=False, index=True)

    # Load Details
    weight = Column(Integer, nullable=False)  # in pounds
    commodity_type = Column(String(100))
    dimensions = Column(String(255))
    num_of_pieces = Column(Integer)
    miles = Column(String(50))  # Store as string to allow for decimal values

    # Pricing
    loadboard_rate = Column(NUMERIC(10, 2), nullable=False, index=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="AVAILABLE", index=True
    )
    # AVAILABLE, PENDING, BOOKED, IN_TRANSIT, DELIVERED, CANCELLED
    booked = Column(Boolean, default=False, index=True)

    # Special Instructions
    notes = Column(Text)

    # Session Information
    session_id = Column(String(255), nullable=True)

    # Visibility
    is_active = Column(Boolean, default=True, index=True)

    # Metadata
    version = Column(Integer, default=1)

    def __repr__(self) -> str:
        return f"<LoadModel(reference_number='{self.reference_number}', origin='{self.origin_city}, {self.origin_state}', destination='{self.destination_city}, {self.destination_state}')>"
